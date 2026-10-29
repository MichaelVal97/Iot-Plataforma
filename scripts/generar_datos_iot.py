#!/usr/bin/env python3
"""
Script de generación de datos IoT realistas.

Genera datos sintéticos de sensores IoT y los inserta en MongoDB en lotes.
Permite configuración mediante variables de entorno o argumentos.
Evita cargar todo en RAM mediante procesamiento por lotes.
Soporta reanudación si se interrumpe.

Requisitos:
- pymongo
- python-dotenv
- faker

Configuración mediante variables de entorno:
- MONGODB_URI: Conexión a MongoDB (requerida)
- NUM_SENSORS: Cantidad de sensores (default: 100)
- TOTAL_DOCUMENTS: Cantidad total de documentos a generar (default: 100000)
- TARGET_GB: Tamaño objetivo en GB (default: 50)
- BATCH_SIZE: Tamaño de lotes para inserción (default: 1000)
- DATABASE: Nombre de base de datos (default: iot_platform)
- COLLECTION_READINGS: Colección de lecturas (default: sensor_readings)
- COLLECTION_SENSORS: Colección de metadatos (default: sensors)

Uso:
    python generar_datos_iot.py --num-sensors 100 --total-documents 10000 --batch-size 1000
    python generar_datos_iot.py  # Usa variables de entorno o defaults
"""

import os
import sys
import argparse
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

# Intenta importar dependencias
try:
    from pymongo import MongoClient, ASCENDING, errors
    from pymongo.errors import DuplicateKeyError, OperationFailure
    from dotenv import load_dotenv
    from faker import Faker
except ImportError as e:
    print(f"Error: Falta una dependencia. Instala con: pip install -r requirements.txt")
    print(f"Detalles: {e}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración por defecto
DEFAULT_MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/iot_platform?retryWrites=true&w=majority"
DEFAULT_NUM_SENSORS = 100
DEFAULT_TOTAL_DOCUMENTS = 100000
DEFAULT_TARGET_GB = 50
DEFAULT_BATCH_SIZE = 1000
DEFAULT_DATABASE = "iot_platform"
DEFAULT_COLLECTION_READINGS = "sensor_readings"
DEFAULT_COLLECTION_SENSORS = "sensors"


class IoTDataGenerator:
    """Generador de datos IoT realistas."""
    
    # Tipos de sensores válidos
    SENSOR_TYPES = ["weather", "air_quality", "energy", "motion", "temperature", "humidity", "pressure"]
    
    # Estados de sensor
    STATES = ["normal", "warning", "error", "maintenance"]
    
    # Rangos realistas para sensores
    SENSOR_RANGES = {
        "temperatura": (15.0, 35.0),  # Celsius
        "humedad": (30.0, 90.0),       # Porcentaje
        "presion": (950.0, 1050.0),    # hPa
        "calidad_aire": (0, 500),      # AQI
        "energia": (0.0, 1.0),         # KW
    }
    
    def __init__(self, num_sensors: int, mongodb_uri: str, database: str, 
                 collection_readings: str, collection_sensors: str):
        """
        Inicializa el generador.
        
        Args:
            num_sensors: Cantidad de sensores a simular
            mongodb_uri: URI de conexión a MongoDB
            database: Nombre de la base de datos
            collection_readings: Nombre de la colección de lecturas
            collection_sensors: Nombre de la colección de metadatos
        """
        self.num_sensors = num_sensors
        self.mongodb_uri = mongodb_uri
        self.database_name = database
        self.collection_readings_name = collection_readings
        self.collection_sensors_name = collection_sensors
        self.faker = Faker()
        self.client = None
        self.db = None
        self.collection_readings = None
        self.collection_sensors = None
        self.sensor_ids = []
        
    def connect(self) -> bool:
        """
        Conecta a MongoDB.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Conectando a MongoDB: {self.mongodb_uri[:50]}...")
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000
            )
            
            # Verificar conexión
            self.client.admin.command('ping')
            logger.info("✓ Conexión a MongoDB exitosa")
            
            # Obtener base de datos y colecciones
            self.db = self.client[self.database_name]
            self.collection_readings = self.db[self.collection_readings_name]
            self.collection_sensors = self.db[self.collection_sensors_name]
            
            return True
        except errors.ServerSelectionTimeoutError:
            logger.error("✗ Timeout: No se puede conectar a MongoDB. Verifica MONGODB_URI")
            return False
        except Exception as e:
            logger.error(f"✗ Error de conexión: {e}")
            return False
    
    def disconnect(self):
        """Desconecta de MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Desconectado de MongoDB")
    
    def create_indexes(self):
        """Crea índices para optimizar consultas."""
        try:
            logger.info("Creando índices...")
            
            # Índice compuesto: sensor_id + timestamp
            self.collection_readings.create_index([("sensor_id", ASCENDING), ("timestamp", ASCENDING)])
            logger.info("✓ Índice creado: sensor_id + timestamp")
            
            # Índice en timestamp
            self.collection_readings.create_index([("timestamp", ASCENDING)])
            logger.info("✓ Índice creado: timestamp")
            
            # Índice en tipo_sensor
            self.collection_readings.create_index([("tipo_sensor", ASCENDING)])
            logger.info("✓ Índice creado: tipo_sensor")
            
            # Índice en sensor_id
            self.collection_readings.create_index([("sensor_id", ASCENDING)])
            logger.info("✓ Índice creado: sensor_id")
            
        except Exception as e:
            logger.error(f"Error al crear índices: {e}")
    
    def generate_sensors_metadata(self) -> List[Dict]:
        """
        Genera metadatos para los sensores.
        
        Returns:
            Lista de documentos de metadatos de sensores
        """
        logger.info(f"Generando metadatos para {self.num_sensors} sensores...")
        sensors = []
        
        for i in range(self.num_sensors):
            sensor_id = f"sensor_{i:06d}"
            sensor_type = random.choice(self.SENSOR_TYPES)
            
            sensor = {
                "sensor_id": sensor_id,
                "tipo_sensor": sensor_type,
                "ubicacion": {
                    "lat": float(self.faker.latitude()),
                    "lon": float(self.faker.longitude()),
                    "ciudad": self.faker.city(),
                    "pais": self.faker.country()
                },
                "estado": "activo",
                "fecha_instalacion": datetime.now() - timedelta(days=random.randint(1, 365)),
                "fabricante": self.faker.company(),
                "modelo": f"Model-{random.randint(1000, 9999)}",
                "ultima_calibracion": datetime.now() - timedelta(days=random.randint(1, 30))
            }
            
            sensors.append(sensor)
            self.sensor_ids.append(sensor_id)
        
        return sensors
    
    def insert_sensors_metadata(self, sensors: List[Dict]):
        """
        Inserta metadatos de sensores en MongoDB.
        
        Args:
            sensors: Lista de documentos de metadatos
        """
        try:
            # Eliminar sensores previos para asegurar datos limpios
            self.collection_sensors.delete_many({})
            
            result = self.collection_sensors.insert_many(sensors, ordered=False)
            logger.info(f"✓ {len(result.inserted_ids)} metadatos de sensores insertados")
        except Exception as e:
            logger.error(f"Error al insertar metadatos: {e}")
    
    def generate_readings_batch(self, batch_number: int, batch_size: int) -> List[Dict]:
        """
        Genera un lote de lecturas de sensores.
        
        Args:
            batch_number: Número de lote (para calcular rango de timestamps)
            batch_size: Tamaño del lote
            
        Returns:
            Lista de documentos de lecturas
        """
        readings = []
        base_time = datetime.now() - timedelta(days=365)
        
        for doc_num in range(batch_size):
            # Calcular timestamp incremental para realismo
            offset_days = (batch_number * batch_size + doc_num) % 365
            timestamp = base_time + timedelta(
                days=offset_days,
                seconds=random.randint(0, 86400)
            )
            
            sensor_id = random.choice(self.sensor_ids)
            sensor_type = self._get_sensor_type(sensor_id)
            
            reading = {
                "sensor_id": sensor_id,
                "timestamp": timestamp,
                "tipo_sensor": sensor_type,
                "temperatura": self._random_value("temperatura"),
                "humedad": self._random_value("humedad"),
                "presion": self._random_value("presion"),
                "calidad_aire": self._random_value("calidad_aire"),
                "energia": self._random_value("energia"),
                "estado": random.choice(self.STATES),
                "ubicacion": {
                    "lat": float(self.faker.latitude()),
                    "lon": float(self.faker.longitude())
                },
                "datos_adicionales": {
                    "velocidad_viento": round(random.uniform(0, 30), 2),
                    "radiacion_solar": round(random.uniform(0, 1000), 2),
                    "precipitacion": round(random.uniform(0, 50), 2)
                },
                "confiabilidad": round(random.uniform(0.8, 1.0), 3)
            }
            
            readings.append(reading)
        
        return readings
    
    def _random_value(self, field: str) -> float:
        """Genera un valor aleatorio realista para un campo."""
        min_val, max_val = self.SENSOR_RANGES[field]
        if isinstance(min_val, int):
            return random.randint(int(min_val), int(max_val))
        else:
            return round(random.uniform(min_val, max_val), 2)
    
    def _get_sensor_type(self, sensor_id: str) -> str:
        """Obtiene el tipo de sensor basado en su ID."""
        # Buscar en la lista de sensores generados
        idx = int(sensor_id.split("_")[1])
        return self.SENSOR_TYPES[idx % len(self.SENSOR_TYPES)]
    
    def get_document_count(self) -> int:
        """Obtiene la cantidad de documentos ya insertados."""
        return self.collection_readings.count_documents({})
    
    def generate_and_insert(self, total_documents: int, batch_size: int, target_gb: float = None):
        """
        Genera e inserta datos en lotes.
        
        Args:
            total_documents: Cantidad total de documentos a generar
            batch_size: Tamaño de cada lote
            target_gb: Tamaño objetivo en GB (informativo)
        """
        try:
            # Contar documentos existentes
            existing_count = self.get_document_count()
            
            if existing_count > 0:
                logger.info(f"ℹ {existing_count} documentos ya existen. Continuando desde donde se interrumpió...")
                start_batch = existing_count // batch_size
            else:
                logger.info("Iniciando generación de datos desde cero")
                start_batch = 0
            
            total_batches = (total_documents + batch_size - 1) // batch_size
            total_to_insert = total_documents - existing_count
            
            logger.info(f"Objetivo: {total_documents} documentos totales")
            logger.info(f"Ya existen: {existing_count} documentos")
            logger.info(f"Falta insertar: {total_to_insert} documentos")
            if target_gb:
                logger.info(f"Objetivo de tamaño: {target_gb} GB")
            logger.info(f"Tamaño de lote: {batch_size} documentos")
            logger.info(f"Total de lotes a procesar: {total_batches}")
            
            for batch_num in range(start_batch, total_batches):
                if batch_num * batch_size >= total_documents:
                    break
                
                # Calcular tamaño del lote (el último puede ser menor)
                current_batch_size = min(batch_size, total_documents - batch_num * batch_size)
                
                # Generar lote
                readings = self.generate_readings_batch(batch_num, current_batch_size)
                
                # Insertar lote
                try:
                    result = self.collection_readings.insert_many(readings, ordered=False)
                    
                    inserted = len(result.inserted_ids)
                    total_so_far = existing_count + (batch_num + 1 - start_batch) * batch_size
                    progress = (total_so_far / total_documents) * 100
                    
                    logger.info(
                        f"Lote {batch_num + 1}/{total_batches}: "
                        f"{inserted} documentos insertados | "
                        f"Total: {total_so_far}/{total_documents} ({progress:.1f}%)"
                    )
                    
                except errors.BulkWriteError as e:
                    # Algunos documentos pueden fallar, pero continuamos
                    logger.warning(f"Errores en lote {batch_num + 1}: {len(e.details.get('writeErrors', []))} duplicados ignorados")
                    
        except KeyboardInterrupt:
            logger.info("\n⚠ Generación interrumpida por el usuario. Puedes continuar después.")
            current_count = self.get_document_count()
            logger.info(f"Documentos insertados hasta ahora: {current_count}")
        except Exception as e:
            logger.error(f"Error durante la generación: {e}")
            raise


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Generador de datos IoT realistas para MongoDB"
    )
    parser.add_argument("--num-sensors", type=int, help="Cantidad de sensores")
    parser.add_argument("--total-documents", type=int, help="Cantidad total de documentos")
    parser.add_argument("--batch-size", type=int, help="Tamaño de lotes")
    parser.add_argument("--target-gb", type=float, help="Tamaño objetivo en GB")
    
    args = parser.parse_args()
    
    # Configuración con prioridad: argumentos > variables de entorno > defaults
    mongodb_uri = os.getenv("MONGODB_URI", DEFAULT_MONGODB_URI)
    num_sensors = args.num_sensors or int(os.getenv("NUM_SENSORS", DEFAULT_NUM_SENSORS))
    total_documents = args.total_documents or int(os.getenv("TOTAL_DOCUMENTS", DEFAULT_TOTAL_DOCUMENTS))
    batch_size = args.batch_size or int(os.getenv("BATCH_SIZE", DEFAULT_BATCH_SIZE))
    target_gb = args.target_gb or float(os.getenv("TARGET_GB", DEFAULT_TARGET_GB))
    database = os.getenv("DATABASE", DEFAULT_DATABASE)
    collection_readings = os.getenv("COLLECTION_READINGS", DEFAULT_COLLECTION_READINGS)
    collection_sensors = os.getenv("COLLECTION_SENSORS", DEFAULT_COLLECTION_SENSORS)
    
    logger.info("=" * 70)
    logger.info("GENERADOR DE DATOS IoT")
    logger.info("=" * 70)
    logger.info(f"MongoDB URI: {mongodb_uri[:60]}...")
    logger.info(f"Base de datos: {database}")
    logger.info(f"Colección (lecturas): {collection_readings}")
    logger.info(f"Colección (sensores): {collection_sensors}")
    logger.info(f"Sensores: {num_sensors}")
    logger.info(f"Documentos objetivo: {total_documents}")
    logger.info(f"Tamaño objetivo: {target_gb} GB")
    logger.info("=" * 70)
    
    # Crear generador
    generator = IoTDataGenerator(
        num_sensors=num_sensors,
        mongodb_uri=mongodb_uri,
        database=database,
        collection_readings=collection_readings,
        collection_sensors=collection_sensors
    )
    
    # Conectar
    if not generator.connect():
        sys.exit(1)
    
    try:
        # Crear índices
        generator.create_indexes()
        
        # Generar e insertar metadatos de sensores
        sensors_metadata = generator.generate_sensors_metadata()
        generator.insert_sensors_metadata(sensors_metadata)
        
        # Generar e insertar lecturas
        generator.generate_and_insert(total_documents, batch_size, target_gb)
        
        # Resumen final
        final_count = generator.get_document_count()
        logger.info("=" * 70)
        logger.info(f"✓ GENERACIÓN COMPLETADA")
        logger.info(f"  Documentos totales: {final_count}")
        logger.info(f"  Sensores: {num_sensors}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        generator.disconnect()


if __name__ == "__main__":
    main()
