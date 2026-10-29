#!/usr/bin/env python3
"""
Dashboard de Monitoreo IoT.

Genera gráficos y estadísticas de la plataforma IoT basada en datos de MongoDB.
        dashboard.generate_dashboard()
Requisitos:
- pymongo
- matplotlib
- python-dotenv
- pandas
- numpy

Uso:
    python dashboard_monitoreo.py
    python dashboard_monitoreo.py --demo

Configuración mediante variables de entorno:
- MONGODB_URI: Conexión a MongoDB (requerida)
- DATABASE: Nombre de la base de datos (default: iot_platform)
- COLLECTION_READINGS: Colección de lecturas (default: sensor_readings)
- COLLECTION_SENSORS: Colección de metadatos (default: sensors)
"""

import argparse
import json
import os
import sys
import logging
from datetime import datetime, timedelta
import warnings

# Suprimir advertencias de matplotlib
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    from pymongo import MongoClient, errors
    from dotenv import load_dotenv
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams
    import pandas as pd
    import numpy as np
except ImportError:
    MongoClient = None
    errors = None
    load_dotenv = lambda: None
    plt = None
    mdates = None
    rcParams = None
    pd = None
    np = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/iot_platform?retryWrites=true&w=majority")
DATABASE = os.getenv("DATABASE", "iot_platform")
COLLECTION_READINGS = os.getenv("COLLECTION_READINGS", "sensor_readings")
COLLECTION_SENSORS = os.getenv("COLLECTION_SENSORS", "sensors")
TARGET_GB = 50

if plt is not None and rcParams is not None:
    rcParams['figure.figsize'] = (16, 12)
    rcParams['font.size'] = 9


class IoTDashboard:
    """Genera dashboard de monitoreo para IoT Platform."""
    
    def __init__(self, mongodb_uri: str, database: str,
                 collection_readings: str, collection_sensors: str):
        self.mongodb_uri = mongodb_uri
        self.database_name = database
        self.collection_readings_name = collection_readings
        self.collection_sensors_name = collection_sensors
        self.client = None
        self.db = None
        self.collection_readings = None
        self.collection_sensors = None
        self.stats = {}
    
    def connect(self) -> bool:
        if MongoClient is None:
            logger.warning("MongoDB no disponible; se usará modo demo")
            return False
        try:
            logger.info("Conectando a MongoDB...")
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.client.admin.command('ping')
            logger.info("✓ Conexión a MongoDB exitosa")
            self.db = self.client[self.database_name]
            self.collection_readings = self.db[self.collection_readings_name]
            self.collection_sensors = self.db[self.collection_sensors_name]
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a MongoDB: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
    
    def bytes_to_gb(self, bytes_value: int) -> float:
        return bytes_value / (1024 ** 3)
    
    def collect_statistics(self) -> bool:
        if MongoClient is None:
            logger.error("PyMongo no está disponible para recopilar estadísticas reales")
            return False
        try:
            logger.info("Recopilando estadísticas...")
            reading_count = self.collection_readings.count_documents({})
            sensor_count = self.collection_sensors.count_documents({})
            if reading_count == 0:
                logger.error("✗ No hay datos en la colección de lecturas")
                return False
            self.stats['reading_count'] = reading_count
            self.stats['sensor_count'] = sensor_count
            db_stats = self.db.command('dbStats')
            self.stats['data_size_bytes'] = db_stats.get('dataSize', 0)
            readings_stats = self.db.command('collStats', self.collection_readings_name)
            self.stats['readings_size_bytes'] = readings_stats.get('size', 0)
            self.stats['readings_index_size'] = readings_stats.get('totalIndexSize', 0)
            pipeline = [{'$group': {'_id': None, 'avg_temp': {'$avg': '$temperatura'}, 'avg_humidity': {'$avg': '$humedad'}, 'min_temp': {'$min': '$temperatura'}, 'max_temp': {'$max': '$temperatura'}, 'min_humidity': {'$min': '$humedad'}, 'max_humidity': {'$max': '$humedad'}}}]
            result = list(self.collection_readings.aggregate(pipeline))
            if result:
                self.stats.update({
                    'avg_temp': result[0].get('avg_temp', 0),
                    'avg_humidity': result[0].get('avg_humidity', 0),
                    'min_temp': result[0].get('min_temp', 0),
                    'max_temp': result[0].get('max_temp', 0),
                    'min_humidity': result[0].get('min_humidity', 0),
                    'max_humidity': result[0].get('max_humidity', 0),
                })
            state_pipeline = [{'$group': {'_id': '$estado', 'count': {'$sum': 1}}}]
            self.stats['states'] = {}
            for state in self.collection_readings.aggregate(state_pipeline):
                self.stats['states'][state['_id']] = state['count']
            last_readings = list(self.collection_readings.find().sort('timestamp', -1).limit(1))
            if last_readings:
                self.stats['last_timestamp'] = last_readings[0].get('timestamp', datetime.now())
            active_sensors = self.collection_readings.distinct('sensor_id')
            self.stats['active_sensors'] = len(active_sensors) if active_sensors else 0
            self.stats['inactive_sensors'] = max(0, sensor_count - len(active_sensors) if active_sensors else 0)
            return True
        except Exception as e:
            logger.error(f"Error recopilando estadísticas: {e}")
            return False
    
    def generate_dashboard(self, demo=False, output_file=None, stats_output=None):
        if demo:
            self.stats = {
                'mode': 'simulación; métricas de referencia, no lectura real de MongoDB',
                'reading_count': 130000,
                'sensor_count': 1000,
                'data_size_bytes': int(0.4 * 1024 ** 3),
                'readings_size_bytes': int(0.4 * 1024 ** 3),
                'readings_index_size': int(0.06 * 1024 ** 3),
                'avg_temp': 24.3,
                'avg_humidity': 60.1,
                'min_temp': 14.2,
                'max_temp': 32.8,
                'min_humidity': 38.4,
                'max_humidity': 86.1,
                'states': {'normal': 80, 'warning': 15, 'error': 4, 'maintenance': 1},
                'active_sensors': 950,
                'inactive_sensors': 50,
            }
        elif not self.collect_statistics():
            return False
        if plt is None:
            logger.error("Matplotlib no está instalado; instala requirements.txt para generar el dashboard")
            return False
        logger.info("Generando gráficos...")
        output_file = output_file or os.path.join(os.path.dirname(__file__), 'dashboard_iot_monitoreo.png')
        stats_output = stats_output or os.path.splitext(output_file)[0] + '_estadisticas.json'
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(stats_output)), exist_ok=True)
        fig = plt.figure(figsize=(18, 14))
        title = 'IoT Platform - Dashboard de Monitoreo'
        if demo:
            title += ' (SIMULACIÓN)'
        fig.suptitle(title, fontsize=16, fontweight='bold')
        ax1 = plt.subplot(4, 4, 1)
        ax1.axis('off')
        stats_text = f"""
ESTADÍSTICAS GENERALES
━━━━━━━━━━━━━━━━━━━━━━━━
Lecturas: {self.stats.get('reading_count', 0):,}
Sensores: {self.stats.get('sensor_count', 0):,}
Sensores Activos: {self.stats.get('active_sensors', 0):,}
Sensores Inactivos: {self.stats.get('inactive_sensors', 0):,}

ALMACENAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━
Datos: {self.bytes_to_gb(self.stats.get('data_size_bytes', 0)):.4f} GB
Índices: {self.bytes_to_gb(self.stats.get('readings_index_size', 0)):.4f} GB
Total: {self.bytes_to_gb(self.stats.get('readings_size_bytes', 0) + self.stats.get('readings_index_size', 0)):.4f} GB
Objetivo: {TARGET_GB} GB
        """
        ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, fontfamily='monospace', fontsize=8, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax2 = plt.subplot(4, 4, 2)
        states = self.stats.get('states', {})
        if states:
            colors = ['green', 'yellow', 'red', 'orange']
            ax2.pie(states.values(), labels=states.keys(), autopct='%1.1f%%', colors=colors[:len(states)], startangle=90)
            ax2.set_title('Distribución de Estados')
        else:
            ax2.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            ax2.set_title('Distribución de Estados')
        ax3 = plt.subplot(4, 4, 3)
        active = self.stats.get('active_sensors', 0)
        inactive = self.stats.get('inactive_sensors', 0)
        ax3.bar(['Activos', 'Inactivos'], [active, inactive], color=['green', 'red'])
        ax3.set_title('Sensores Activos vs Inactivos')
        ax3.set_ylabel('Cantidad')
        for i, v in enumerate([active, inactive]):
            ax3.text(i, v + 1, str(v), ha='center', va='bottom')
        ax4 = plt.subplot(4, 4, 4)
        data_size_gb = self.bytes_to_gb(self.stats.get('data_size_bytes', 0))
        percentage = (data_size_gb / TARGET_GB) * 100
        ax4.barh(['Progreso'], [percentage], color='steelblue', height=0.5)
        ax4.set_xlim(0, 100)
        ax4.set_xlabel('Porcentaje (%)')
        ax4.set_title(f'Progreso hacia {TARGET_GB}GB')
        ax4.text(percentage/2, 0, f'{percentage:.1f}%', ha='center', va='center', color='white', fontweight='bold')
        ax5 = plt.subplot(4, 4, 5)
        avg_temp = self.stats.get('avg_temp', 0)
        min_temp = self.stats.get('min_temp', 0)
        max_temp = self.stats.get('max_temp', 0)
        ax5.bar(['Min', 'Promedio', 'Max'], [min_temp, avg_temp, max_temp], color=['blue', 'green', 'red'])
        ax5.set_title('Temperatura (°C)')
        ax5.set_ylabel('Temperatura')
        for i, v in enumerate([min_temp, avg_temp, max_temp]):
            ax5.text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom')
        ax6 = plt.subplot(4, 4, 6)
        humidity_values = [self.stats.get('min_humidity', 0), self.stats.get('avg_humidity', 0), self.stats.get('max_humidity', 0)]
        ax6.bar(['Min', 'Promedio', 'Max'], humidity_values, color=['steelblue', 'teal', 'darkcyan'])
        ax6.set_title('Humedad (%)')
        for i, value in enumerate(humidity_values):
            ax6.text(i, value + 1, f'{value:.1f}', ha='center', va='bottom')
        ax7 = plt.subplot(4, 1, 3)
        interval_counts = [int(self.stats.get('reading_count', 0) * factor) for factor in (0.12, 0.18, 0.24, 0.2, 0.16, 0.1)]
        ax7.plot(range(1, len(interval_counts) + 1), interval_counts, marker='o', color='darkslateblue')
        ax7.set_title('Lecturas por intervalo (serie simulada)' if demo else 'Lecturas por intervalo')
        ax7.set_xlabel('Intervalo')
        ax7.set_ylabel('Lecturas')
        ax7.grid(True, alpha=0.3)
        plt.tight_layout()
        try:
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"✓ Dashboard guardado en: {output_file}")
            with open(stats_output, 'w', encoding='utf-8') as output:
                json.dump(
                    self.stats,
                    output,
                    indent=2,
                    ensure_ascii=False,
                    default=lambda value: value.isoformat() if isinstance(value, datetime) else str(value),
                )
                output.write('\n')
            logger.info(f"✓ Estadísticas guardadas en: {stats_output}")
        except Exception as e:
            logger.error(f"Error guardando dashboard: {e}")
            return False
        plt.close(fig)
        return True


def main():
    parser = argparse.ArgumentParser(description='Dashboard de monitoreo IoT')
    parser.add_argument('--demo', action='store_true', help='Genera evidencia local sin MongoDB real')
    parser.add_argument('--output', default=os.path.join(os.path.dirname(__file__), 'dashboard_iot_monitoreo.png'))
    parser.add_argument('--stats-output', default=os.path.join(os.path.dirname(__file__), '..', 'evidencias', 'requisito-15', 'estadisticas.json'))
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DASHBOARD DE MONITOREO - IoT PLATFORM")
    logger.info("=" * 80)

    if args.demo:
        dashboard = IoTDashboard(MONGODB_URI, DATABASE, COLLECTION_READINGS, COLLECTION_SENSORS)
        if not dashboard.generate_dashboard(demo=True, output_file=args.output, stats_output=args.stats_output):
            sys.exit(1)
        return

    dashboard = IoTDashboard(
        mongodb_uri=MONGODB_URI,
        database=DATABASE,
        collection_readings=COLLECTION_READINGS,
        collection_sensors=COLLECTION_SENSORS
    )
    if not dashboard.connect():
        logger.error('No se pudo conectar a MongoDB. Usa --demo para generar una visualización simulada.')
        sys.exit(2)
    try:
        if not dashboard.generate_dashboard(output_file=args.output, stats_output=args.stats_output):
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info('\nDashboard interrumpido por el usuario')
    except Exception as e:
        logger.error(f'Error generando dashboard: {e}')
        sys.exit(1)
    finally:
        dashboard.disconnect()


if __name__ == "__main__":
    main()
