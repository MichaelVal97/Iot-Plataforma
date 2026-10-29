#!/usr/bin/env python3
"""
Script de verificación del tamaño de datos en MongoDB.

Muestra estadísticas detalladas sobre:
- Cantidad de documentos
- Tamaño de datos (lógico)
- Tamaño de índices
- Tamaño total de almacenamiento
- Porcentaje respecto a objetivo de 50 GB
- Diferencias entre tamaño lógico y físico

Requisitos:
- pymongo
- python-dotenv

Uso:
    python verificar_tamano_mongodb.py
    python verificar_tamano_mongodb.py --demo

Configuración mediante variables de entorno:
- MONGODB_URI: Conexión a MongoDB (requerida)
- DATABASE: Nombre de base de datos (default: iot_platform)
- COLLECTION_READINGS: Colección de lecturas (default: sensor_readings)
- COLLECTION_SENSORS: Colección de metadatos (default: sensors)
"""

import argparse
import os
import sys
import logging
from datetime import datetime

try:
    from pymongo import MongoClient, errors
    from dotenv import load_dotenv
except ImportError:
    MongoClient = None
    errors = None
    load_dotenv = lambda: None

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/iot_platform?retryWrites=true&w=majority")
DATABASE = os.getenv("DATABASE", "iot_platform")
COLLECTION_READINGS = os.getenv("COLLECTION_READINGS", "sensor_readings")
COLLECTION_SENSORS = os.getenv("COLLECTION_SENSORS", "sensors")
TARGET_GB = 50


class MongoDBSizeVerifier:
    """Verifica y reporta el tamaño de datos en MongoDB."""
    
    def __init__(self, mongodb_uri: str, database: str, collection_readings: str, collection_sensors: str):
        self.mongodb_uri = mongodb_uri
        self.database_name = database
        self.collection_readings_name = collection_readings
        self.collection_sensors_name = collection_sensors
        self.client = None
        self.db = None
    
    def connect(self) -> bool:
        if MongoClient is None:
            logger.warning("No hay pymongo instalado; ejecutando modo demo")
            return False
        try:
            logger.info("Conectando a MongoDB...")
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
            self.client.admin.command('ping')
            logger.info("✓ Conexión a MongoDB exitosa")
            self.db = self.client[self.database_name]
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a MongoDB: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
    
    def bytes_to_gb(self, bytes_value: int) -> float:
        return bytes_value / (1024 ** 3)
    
    def bytes_to_mb(self, bytes_value: int) -> float:
        return bytes_value / (1024 ** 2)
    
    def get_collection_stats(self, collection_name: str) -> dict:
        if self.db is None:
            return {'document_count': 0, 'avg_doc_size': 0, 'storage_size': 0, 'total_index_size': 0, 'doc_size': 0, 'ns': collection_name}
        try:
            stats = self.db.command('collStats', collection_name)
            return {'document_count': stats.get('count', 0), 'avg_doc_size': stats.get('avgObjSize', 0), 'storage_size': stats.get('size', 0), 'total_index_size': stats.get('totalIndexSize', 0), 'doc_size': stats.get('size', 0), 'ns': stats.get('ns', '')}
        except Exception:
            return {'document_count': 0, 'avg_doc_size': 0, 'storage_size': 0, 'total_index_size': 0, 'doc_size': 0, 'ns': collection_name}
    
    def get_database_stats(self) -> dict:
        if self.db is None:
            return {}
        try:
            return self.db.command('dbStats')
        except Exception:
            return {}
    
    def verify_and_report(self):
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN DE TAMAÑO DE DATOS - IoT PLATFORM")
        logger.info("=" * 80)
        logger.info(f"Base de datos: {self.database_name}")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        readings_stats = self.get_collection_stats(self.collection_readings_name)
        sensors_stats = self.get_collection_stats(self.collection_sensors_name)
        db_stats = self.get_database_stats()
        total_documents = readings_stats['document_count'] + sensors_stats['document_count']
        total_data_size = readings_stats['doc_size'] + sensors_stats['doc_size']
        total_index_size = readings_stats['total_index_size'] + sensors_stats['total_index_size']
        total_storage = total_data_size + total_index_size

        logger.info("📊 COLECCIÓN: sensor_readings")
        logger.info("-" * 80)
        logger.info(f"  Documentos: {readings_stats['document_count']:,}")
        logger.info(f"  Tamaño promedio por documento: {readings_stats['avg_doc_size']:,.0f} bytes ({self.bytes_to_mb(readings_stats['avg_doc_size']):.2f} MB)")
        logger.info(f"  Tamaño lógico de datos: {self.bytes_to_mb(readings_stats['doc_size']):.2f} MB ({self.bytes_to_gb(readings_stats['doc_size']):.2f} GB)")
        logger.info(f"  Tamaño de índices: {self.bytes_to_mb(readings_stats['total_index_size']):.2f} MB ({self.bytes_to_gb(readings_stats['total_index_size']):.4f} GB)")
        logger.info(f"  Tamaño total: {self.bytes_to_mb(readings_stats['doc_size'] + readings_stats['total_index_size']):.2f} MB ({self.bytes_to_gb(readings_stats['doc_size'] + readings_stats['total_index_size']):.4f} GB)")
        logger.info("")

        logger.info("📈 RESUMEN TOTAL")
        logger.info("-" * 80)
        logger.info(f"  Total de documentos: {total_documents:,}")
        logger.info(f"  Tamaño lógico de datos: {self.bytes_to_mb(total_data_size):.2f} MB ({self.bytes_to_gb(total_data_size):.4f} GB)")
        logger.info(f"  Tamaño de índices: {self.bytes_to_mb(total_index_size):.2f} MB ({self.bytes_to_gb(total_index_size):.4f} GB)")
        logger.info(f"  Tamaño total: {self.bytes_to_mb(total_storage):.2f} MB ({self.bytes_to_gb(total_storage):.4f} GB)")
        logger.info("")

        target_bytes = TARGET_GB * (1024 ** 3)
        percentage = (total_data_size / target_bytes) * 100 if target_bytes else 0.0
        logger.info("🎯 ANÁLISIS RESPECTO A OBJETIVO")
        logger.info("-" * 80)
        logger.info(f"  Objetivo: {TARGET_GB} GB")
        logger.info(f"  Datos actuales (lógico): {self.bytes_to_gb(total_data_size):.4f} GB")
        logger.info(f"  Porcentaje: {percentage:.2f}%")
        logger.info(f"  Falta: {self.bytes_to_gb(max(target_bytes - total_data_size, 0)):.4f} GB")
        goal_reached = total_data_size >= target_bytes
        if goal_reached:
            logger.info(f"  ✓ OBJETIVO CUMPLIDO: Se alcanzó o superó los {TARGET_GB} GB")
        else:
            logger.info(f"  ✗ OBJETIVO PENDIENTE: faltan {self.bytes_to_gb(target_bytes - total_data_size):.4f} GB")
        logger.info("")

        if db_stats:
            logger.info(f"  Tamaño reportado por BD: {self.bytes_to_gb(db_stats.get('dataSize', 0)):.4f} GB")
            logger.info(f"  Tamaño de almacenamiento (BD): {self.bytes_to_gb(db_stats.get('storageSize', 0)):.4f} GB")

        return {
            'total_documents': total_documents,
            'total_data_size_gb': self.bytes_to_gb(total_data_size),
            'total_index_size_gb': self.bytes_to_gb(total_index_size),
            'total_storage_gb': self.bytes_to_gb(total_storage),
            'percentage_of_target': percentage,
            'target_gb': TARGET_GB,
            'goal_reached': goal_reached,
        }


def main():
    parser = argparse.ArgumentParser(description='Verifica el tamaño de datos en MongoDB')
    parser.add_argument('--demo', action='store_true', help='Genera una validación local sin MongoDB real')
    parser.add_argument('--output', default=None, help='Ruta del archivo de salida para la evidencia')
    parser.add_argument('--current-gb', type=float, default=0.4, help='Tamaño actual de referencia para la proyección demo')
    args = parser.parse_args()

    logger.info("Inicializando verificador de tamaño...")
    verifier = MongoDBSizeVerifier(mongodb_uri=MONGODB_URI, database=DATABASE, collection_readings=COLLECTION_READINGS, collection_sensors=COLLECTION_SENSORS)

    if args.demo:
        current_gb = max(args.current_gb, 0)
        percentage = current_gb / TARGET_GB * 100
        scale_factor = TARGET_GB / current_gb if current_gb else None
        goal_reached = current_gb >= TARGET_GB
        status = 'OBJETIVO CUMPLIDO' if goal_reached else 'OBJETIVO NO ALCANZADO'
        report = [
            'PROYECCIÓN SIMULADA DE ESCALAMIENTO IoT',
            'Modo: simulación local; no consulta ni modifica MongoDB.',
            f'Tamaño base de referencia: {current_gb:.2f} GB (valor indicado en la matriz).',
            f'Objetivo: {TARGET_GB:.2f} GB',
            f'Progreso de referencia: {percentage:.2f}%',
            f'Faltante estimado: {max(TARGET_GB - current_gb, 0):.2f} GB',
            f'Factor de escala estimado: {scale_factor:.2f}x' if scale_factor is not None else 'Factor de escala: indefinido si el tamaño base es cero.',
            f'Estado: {status}; esta proyección no representa datos almacenados.',
        ]
        logger.info('\n'.join(report))
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as fh:
                fh.write('\n'.join(report) + '\n')
        return

    if not verifier.connect():
        logger.error('No se pudo conectar a MongoDB. Usa --demo para una proyección explícitamente simulada.')
        sys.exit(2)

    try:
        result = verifier.verify_and_report()
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as fh:
                fh.write('VERIFICACIÓN DE TAMAÑO DE DATOS\n')
                fh.write(f"Objetivo: {result['target_gb']} GB\n")
                fh.write(f"Datos actuales: {result['total_data_size_gb']:.2f} GB\n")
                fh.write(f"Índices: {result['total_index_size_gb']:.2f} GB\n")
                fh.write(f"Total: {result['total_storage_gb']:.2f} GB\n")
                fh.write(f"Estado: {'OBJETIVO CUMPLIDO' if result['goal_reached'] else 'OBJETIVO PENDIENTE'}\n")
        sys.exit(0 if result['goal_reached'] else 1)
    except Exception as e:
        logger.error(f"Error durante verificación: {e}")
        sys.exit(1)
    finally:
        verifier.disconnect()


if __name__ == "__main__":
    main()
