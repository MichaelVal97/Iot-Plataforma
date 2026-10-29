#!/usr/bin/env python3
"""Exporta datos IoT de MongoDB a un Data Lake local o en Amazon S3."""

import argparse
import logging
import os
import posixpath
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import boto3
import pandas as pd
from bson import json_util
from dotenv import load_dotenv
from pymongo import MongoClient


LOGGER = logging.getLogger("data_lake_manager")
METRICS = ("temperatura", "humedad", "presion", "calidad_aire", "energia")


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def map_sensor(document: Dict) -> Dict:
    location = document.get("ubicacion") or {}
    return {
        "sensor_id": document.get("sensor_id"),
        "tipo_sensor": document.get("tipo_sensor"),
        "estado": document.get("estado"),
        "lat": location.get("lat"),
        "lon": location.get("lon"),
        "ciudad": location.get("ciudad"),
        "pais": location.get("pais"),
        "fecha_instalacion": as_utc(document.get("fecha_instalacion")),
        "fabricante": document.get("fabricante"),
        "modelo": document.get("modelo"),
        "ultima_calibracion": as_utc(document.get("ultima_calibracion")),
    }


def map_reading(document: Dict) -> Dict:
    location = document.get("ubicacion") or {}
    extra = document.get("datos_adicionales") or {}
    return {
        "reading_id": str(document.get("_id", "")),
        "sensor_id": document.get("sensor_id"),
        "timestamp": as_utc(document.get("timestamp")),
        "tipo_sensor": document.get("tipo_sensor"),
        "temperatura": document.get("temperatura"),
        "humedad": document.get("humedad"),
        "presion": document.get("presion"),
        "calidad_aire": document.get("calidad_aire"),
        "energia": document.get("energia"),
        "estado": document.get("estado"),
        "lat": location.get("lat"),
        "lon": location.get("lon"),
        "velocidad_viento": extra.get("velocidad_viento"),
        "radiacion_solar": extra.get("radiacion_solar"),
        "precipitacion": extra.get("precipitacion"),
        "confiabilidad": document.get("confiabilidad"),
    }


def add_to_daily_summary(summaries: Dict, reading: Dict) -> None:
    timestamp = reading.get("timestamp")
    if timestamp is None:
        return

    key = (timestamp.date().isoformat(), reading.get("tipo_sensor") or "desconocido")
    summary = summaries[key]
    summary["fecha"] = key[0]
    summary["tipo_sensor"] = key[1]
    summary["cantidad_lecturas"] += 1
    for metric in METRICS:
        value = reading.get(metric)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            summary[f"{metric}_suma"] += value
            summary[f"{metric}_conteo"] += 1


def finalize_daily_summaries(summaries: Dict) -> List[Dict]:
    rows = []
    for summary in summaries.values():
        row = {
            "fecha": summary["fecha"],
            "tipo_sensor": summary["tipo_sensor"],
            "cantidad_lecturas": summary["cantidad_lecturas"],
        }
        for metric in METRICS:
            count = summary[f"{metric}_conteo"]
            row[f"{metric}_promedio"] = (
                summary[f"{metric}_suma"] / count if count else None
            )
        rows.append(row)
    return rows


def write_parquet(
    rows: List[Dict],
    storage: str,
    stage: str,
    collection: str,
    load_id: str,
    part_number: int,
    output: Path,
    bucket: Optional[str],
    prefix: str,
    s3_client,
) -> None:
    if not rows:
        return

    relative_path = Path(stage) / collection / f"load_id={load_id}" / f"part-{part_number:05d}.parquet"
    if storage == "local":
        destination = output / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(destination, index=False, compression="snappy")
        LOGGER.info("Escrito: %s (%s filas)", destination, len(rows))
        return

    key = posixpath.join(prefix, relative_path.as_posix())
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_file = Path(temporary_directory) / "batch.parquet"
        pd.DataFrame(rows).to_parquet(temporary_file, index=False, compression="snappy")
        s3_client.upload_file(str(temporary_file), bucket, key)
    LOGGER.info("Subido: s3://%s/%s (%s filas)", bucket, key, len(rows))


def export_collection(
    database,
    collection_name: str,
    mapper,
    args,
    load_id: str,
    s3_client,
) -> int:
    cursor = database[collection_name].find().batch_size(args.batch_size)
    if args.limit:
        cursor = cursor.limit(args.limit)

    summaries = defaultdict(
        lambda: {
            "cantidad_lecturas": 0,
            **{f"{metric}_{part}": 0 for metric in METRICS for part in ("suma", "conteo")},
        }
    )
    raw_batch = []
    processed_batch = []
    total = 0
    part_number = 0

    def flush_batch() -> None:
        nonlocal part_number
        write_parquet(
            raw_batch, args.storage, "raw", collection_name, load_id, part_number,
            args.output, args.bucket, args.prefix, s3_client,
        )
        write_parquet(
            processed_batch, args.storage, "processed", collection_name, load_id,
            part_number, args.output, args.bucket, args.prefix, s3_client,
        )
        raw_batch.clear()
        processed_batch.clear()
        part_number += 1

    for document in cursor:
        raw_batch.append(
            {
                "source_collection": collection_name,
                "document_id": str(document.get("_id", "")),
                "document_json": json_util.dumps(document),
            }
        )
        processed = mapper(document)
        processed_batch.append(processed)
        if collection_name == args.collection_readings:
            add_to_daily_summary(summaries, processed)
        total += 1
        if len(raw_batch) >= args.batch_size:
            flush_batch()

    flush_batch()
    if collection_name == args.collection_readings:
        write_parquet(
            finalize_daily_summaries(summaries), args.storage, "curated",
            "daily_reading_metrics", load_id, 0, args.output, args.bucket,
            args.prefix, s3_client,
        )
    LOGGER.info("Colección %s exportada: %s documentos", collection_name, total)
    return total


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Exporta sensores y lecturas MongoDB a zonas Parquet locales o S3."
    )
    parser.add_argument("--storage", choices=("local", "s3"), default="local")
    parser.add_argument(
        "--output", type=Path,
        default=Path(os.getenv("DATA_LAKE_LOCAL_PATH", "data_lake")),
        help="Directorio local para las zonas raw, processed y curated.",
    )
    parser.add_argument("--bucket", default=os.getenv("AWS_DATA_LAKE_BUCKET"))
    parser.add_argument("--prefix", default=os.getenv("AWS_DATA_LAKE_PREFIX", "iot-data"))
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--limit", type=int, help="Limita documentos por colección para pruebas.")
    args = parser.parse_args()
    args.collection_sensors = os.getenv("COLLECTION_SENSORS", "sensors")
    args.collection_readings = os.getenv("COLLECTION_READINGS", "sensor_readings")

    if args.batch_size < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--batch-size y --limit deben ser mayores que cero")
    if args.storage == "s3" and not args.bucket:
        parser.error("Configura AWS_DATA_LAKE_BUCKET o indica --bucket para usar S3")

    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DATABASE", "iot_platform")
    if not mongodb_uri:
        parser.error("Configura MONGODB_URI en el entorno o en .env")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    s3_client = None
    if args.storage == "s3":
        session = boto3.Session(
            profile_name=os.getenv("AWS_PROFILE") or None,
            region_name=os.getenv("AWS_REGION") or None,
        )
        s3_client = session.client("s3")

    load_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    try:
        database = mongo_client[database_name]
        database.command("ping")
        sensor_count = export_collection(
            database, args.collection_sensors, map_sensor, args, load_id, s3_client
        )
        reading_count = export_collection(
            database, args.collection_readings, map_reading, args, load_id, s3_client
        )
        LOGGER.info(
            "Data Lake listo: %s sensores y %s lecturas (%s)",
            sensor_count,
            reading_count,
            f"s3://{args.bucket}/{args.prefix}" if args.storage == "s3" else args.output,
        )
    finally:
        mongo_client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())