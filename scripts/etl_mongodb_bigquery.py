#!/usr/bin/env python3
"""Carga las colecciones IoT de MongoDB en un esquema analitico de BigQuery."""

import argparse
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from google.cloud import bigquery
from pymongo import MongoClient


LOGGER = logging.getLogger("etl_mongodb_bigquery")

DIM_SENSOR_SCHEMA = [
    bigquery.SchemaField("sensor_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("tipo_sensor", "STRING"),
    bigquery.SchemaField("estado", "STRING"),
    bigquery.SchemaField("lat", "FLOAT"),
    bigquery.SchemaField("lon", "FLOAT"),
    bigquery.SchemaField("ciudad", "STRING"),
    bigquery.SchemaField("pais", "STRING"),
    bigquery.SchemaField("fecha_instalacion", "TIMESTAMP"),
    bigquery.SchemaField("fabricante", "STRING"),
    bigquery.SchemaField("modelo", "STRING"),
    bigquery.SchemaField("ultima_calibracion", "TIMESTAMP"),
]

FACT_READING_SCHEMA = [
    bigquery.SchemaField("reading_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("sensor_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("tipo_sensor", "STRING"),
    bigquery.SchemaField("temperatura", "FLOAT"),
    bigquery.SchemaField("humedad", "FLOAT"),
    bigquery.SchemaField("presion", "FLOAT"),
    bigquery.SchemaField("calidad_aire", "INTEGER"),
    bigquery.SchemaField("energia", "FLOAT"),
    bigquery.SchemaField("estado", "STRING"),
    bigquery.SchemaField("lat", "FLOAT"),
    bigquery.SchemaField("lon", "FLOAT"),
    bigquery.SchemaField("velocidad_viento", "FLOAT"),
    bigquery.SchemaField("radiacion_solar", "FLOAT"),
    bigquery.SchemaField("precipitacion", "FLOAT"),
    bigquery.SchemaField("confiabilidad", "FLOAT"),
]


def as_timestamp(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def map_sensor(document: Dict) -> Dict:
    location = document.get("ubicacion") or {}
    return {
        "sensor_id": document["sensor_id"],
        "tipo_sensor": document.get("tipo_sensor"),
        "estado": document.get("estado"),
        "lat": location.get("lat"),
        "lon": location.get("lon"),
        "ciudad": location.get("ciudad"),
        "pais": location.get("pais"),
        "fecha_instalacion": as_timestamp(document.get("fecha_instalacion")),
        "fabricante": document.get("fabricante"),
        "modelo": document.get("modelo"),
        "ultima_calibracion": as_timestamp(document.get("ultima_calibracion")),
    }


def map_reading(document: Dict) -> Dict:
    location = document.get("ubicacion") or {}
    extra = document.get("datos_adicionales") or {}
    return {
        "reading_id": str(document["_id"]),
        "sensor_id": document["sensor_id"],
        "timestamp": as_timestamp(document["timestamp"]),
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


def load_batches(
    client: bigquery.Client,
    documents: Iterable[Dict],
    destination: str,
    schema: List[bigquery.SchemaField],
    mapper,
    batch_size: int,
) -> int:
    batch = []
    total = 0
    for document in documents:
        batch.append(mapper(document))
        if len(batch) == batch_size:
            load_batch(client, destination, schema, batch)
            total += len(batch)
            LOGGER.info("%s: %s filas cargadas", destination, total)
            batch = []
    if batch:
        load_batch(client, destination, schema, batch)
        total += len(batch)
        LOGGER.info("%s: %s filas cargadas", destination, total)
    return total


def load_batch(
    client: bigquery.Client,
    destination: str,
    schema: List[bigquery.SchemaField],
    rows: List[Dict],
) -> None:
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    client.load_table_from_json(rows, destination, job_config=job_config).result()


def replace_table(
    client: bigquery.Client,
    table_id: str,
    schema: List[bigquery.SchemaField],
) -> None:
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(bigquery.Table(table_id, schema=schema))


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Replica sensor_readings y sensors de MongoDB a BigQuery."
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, help="Limita filas por coleccion para pruebas")
    args = parser.parse_args()
    if args.batch_size < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--batch-size y --limit deben ser mayores que cero")

    mongodb_uri = os.getenv("MONGODB_URI")
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET", "iot_warehouse")
    location = os.getenv("BIGQUERY_LOCATION", "US")
    database_name = os.getenv("MONGODB_DATABASE", "iot_platform")
    if not mongodb_uri or not project_id:
        parser.error("Configura MONGODB_URI y BIGQUERY_PROJECT_ID en el entorno o .env")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    try:
        database = mongo_client[database_name]
        database.command("ping")

        warehouse = bigquery.Client(project=project_id)
        dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
        dataset_ref.location = location
        warehouse.create_dataset(dataset_ref, exists_ok=True)

        dim_table = f"{project_id}.{dataset_id}.dim_sensors"
        fact_table = f"{project_id}.{dataset_id}.fact_readings"
        replace_table(warehouse, dim_table, DIM_SENSOR_SCHEMA)
        replace_table(warehouse, fact_table, FACT_READING_SCHEMA)

        sensor_cursor = database[os.getenv("COLLECTION_SENSORS", "sensors")].find()
        reading_cursor = database[os.getenv("COLLECTION_READINGS", "sensor_readings")].find()
        if args.limit:
            sensor_cursor = sensor_cursor.limit(args.limit)
            reading_cursor = reading_cursor.limit(args.limit)

        sensor_count = load_batches(
            warehouse, sensor_cursor, dim_table, DIM_SENSOR_SCHEMA, map_sensor, args.batch_size
        )
        reading_count = load_batches(
            warehouse, reading_cursor, fact_table, FACT_READING_SCHEMA, map_reading, args.batch_size
        )
        LOGGER.info(
            "Carga completa: %s sensores y %s lecturas en %s.%s",
            sensor_count,
            reading_count,
            project_id,
            dataset_id,
        )
    finally:
        mongo_client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())