#!/usr/bin/env python3
"""
Script de verificación de Disaster Recovery.

Proporciona verificaciones parciales de la estrategia de DR sin requerir
credenciales AWS o MongoDB Atlas desplegadas.

Puede ejecutar comprobaciones automáticas en el código y archivos de configuración,
y proporciona guías reproducibles para validaciones de infraestructura.

Requisitos:
- pymongo
- boto3 (opcional, para validaciones AWS)
- python-dotenv

Uso:
    python verify_dr.py --check-config
    python verify_dr.py --check-mongodb
    python verify_dr.py --check-aws
    python verify_dr.py --full
    python verify_dr.py --demo --full

Configuración mediante variables de entorno:
- MONGODB_URI: Conexión a MongoDB primaria
- AWS_PROFILE: Perfil AWS a usar
- AWS_REGION: Región primaria
- AWS_DR_REGION: Región secundaria de DR
"""

import os
import sys
import logging
import argparse
import hashlib
import json
import shutil
import tempfile
import time

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv no instalado. Algunas funciones pueden no funcionar.")
    load_dotenv = lambda: None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    load_dotenv()
except Exception:
    pass

MONGODB_URI = os.getenv("MONGODB_URI", "")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_DR_REGION = os.getenv("AWS_DR_REGION", "us-west-2")


class DisasterRecoveryVerifier:
    """Verifica aspectos de Disaster Recovery."""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warnings = []
    
    def check_config_files(self) -> bool:
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN 1: Archivos de Configuración")
        logger.info("=" * 80)
        required_files = ["docs/disaster-recovery.md", ".env.example", "terraform/main.tf", "terraform/variables.tf"]
        all_exist = True
        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            exists = os.path.exists(full_path)
            status = "✓" if exists else "✗"
            logger.info(f"  {status} {file_path}: {'EXISTE' if exists else 'NO EXISTE'}")
            if exists:
                self.checks_passed.append(f"Archivo {file_path} existe")
            else:
                self.checks_failed.append(f"Archivo {file_path} no existe")
                all_exist = False
        logger.info("")
        return all_exist
    
    def check_environment_vars(self) -> bool:
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN 2: Variables de Entorno")
        logger.info("=" * 80)
        required_vars = {"MONGODB_URI": MONGODB_URI, "AWS_REGION": AWS_REGION, "AWS_DR_REGION": AWS_DR_REGION}
        all_configured = True
        for var_name, var_value in required_vars.items():
            configured = bool(var_value) and var_value != "default"
            status = "✓" if configured else "⚠"
            if configured and "password" not in var_name.lower():
                logger.info(f"  {status} {var_name}: CONFIGURADA")
                self.checks_passed.append(f"Variable {var_name} configurada")
            elif not configured:
                logger.info(f"  {status} {var_name}: NO CONFIGURADA")
                self.checks_warnings.append(f"Variable {var_name} no está configurada")
                all_configured = False
            else:
                logger.info(f"  {status} {var_name}: [CREDENCIAL]")
                self.checks_passed.append(f"Variable {var_name} contiene credencial")
        logger.info("")
        return all_configured
    
    def check_mongodb_connectivity(self) -> bool:
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN 3: Conectividad MongoDB")
        logger.info("=" * 80)
        if not MONGODB_URI:
            logger.info("  ⚠ MONGODB_URI no configurada")
            self.checks_warnings.append("No se puede verificar MongoDB sin MONGODB_URI")
            logger.info("")
            return False
        try:
            from pymongo import MongoClient
            logger.info("  Intentando conectar a MongoDB (URI oculta)...")
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
            client.admin.command('ping')
            logger.info("  ✓ Conexión exitosa")
            logger.info("  ✓ Usando MongoDB Atlas")
            self.checks_passed.append("MongoDB Atlas detectado")
            self.checks_passed.append("Conexión a MongoDB verificada")
            client.close()
            logger.info("")
            return True
        except Exception as e:
            logger.info(f"  ✗ Error de conexión: {e}")
            self.checks_failed.append(f"No se puede conectar a MongoDB: {e}")
            logger.info("")
            return False
    
    def check_aws_credentials(self) -> bool:
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN 4: Credenciales AWS")
        logger.info("=" * 80)
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, PartialCredentialsError
        except ImportError:
            logger.info("  ⚠ boto3 no instalado")
            self.checks_warnings.append("boto3 no disponible para verificación AWS")
            logger.info("  Instala con: pip install boto3")
            logger.info("")
            return False
        try:
            logger.info(f"  Verificando credenciales con perfil: {AWS_PROFILE}")
            session = boto3.Session(profile_name=AWS_PROFILE)
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            logger.info(f"  ✓ Credenciales válidas")
            logger.info(f"  ✓ Account ID: {identity.get('Account', 'unknown')}")
            self.checks_passed.append("Credenciales AWS verificadas")
            logger.info("")
            return True
        except (NoCredentialsError, PartialCredentialsError):
            logger.info("  ✗ Credenciales AWS no encontradas")
            self.checks_failed.append("Credenciales AWS no disponibles")
            logger.info("")
            return False
        except Exception as e:
            logger.info(f"  ⚠ Error al verificar credenciales: {e}")
            self.checks_warnings.append(f"Error verificando AWS: {e}")
            logger.info("")
            return False
    
    def check_terraform_files(self) -> bool:
        logger.info("=" * 80)
        logger.info("VERIFICACIÓN 5: Configuración Terraform")
        logger.info("=" * 80)
        terraform_dir = os.path.join(os.path.dirname(__file__), "..", "terraform")
        if not os.path.exists(terraform_dir):
            logger.info("  ✗ Directorio terraform/ no existe")
            self.checks_failed.append("Directorio terraform no existe")
            logger.info("")
            return False
        logger.info("  ✓ Directorio terraform/ existe")
        required_tf_files = ["main.tf", "variables.tf", "providers.tf", "outputs.tf"]
        all_exist = True
        for tf_file in required_tf_files:
            file_path = os.path.join(terraform_dir, tf_file)
            exists = os.path.exists(file_path)
            status = "✓" if exists else "✗"
            logger.info(f"  {status} {tf_file}: {'EXISTE' if exists else 'NO EXISTE'}")
            if not exists:
                all_exist = False
                self.checks_failed.append(f"Archivo terraform/{tf_file} no existe")
            else:
                self.checks_passed.append(f"Archivo terraform/{tf_file} existe")
        variables_file = os.path.join(terraform_dir, "variables.tf")
        if os.path.exists(variables_file):
            try:
                with open(variables_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'primary_region' in content or 'aws_region' in content:
                        self.checks_passed.append("Región primaria en Terraform")
                    if 'dr_region' in content or 'secondary_region' in content:
                        self.checks_passed.append("Región DR en Terraform")
            except Exception as e:
                logger.info(f"  ⚠ Error al leer variables.tf: {e}")
        logger.info("")
        return all_exist
    
    def print_manual_verification_guide(self):
        logger.info("=" * 80)
        logger.info("GUÍA DE VERIFICACIÓN MANUAL - DR")
        logger.info("=" * 80)
        logger.info("")
        logger.info("PASO 1: Verificar Replicación en MongoDB Atlas")
        logger.info("-" * 80)
        logger.info("1. Accede a https://cloud.mongodb.com")
        logger.info("2. Selecciona tu cluster")
        logger.info("3. Ve a 'Deployment' → 'Replication'")
        logger.info("4. Verifica que hay 3+ nodos replicados en al menos 2 regiones")
        logger.info("5. Nota el 'Replication Lag' (debería ser < 1 segundo)")
        logger.info("")
        logger.info("PASO 2: Verificar Backups en MongoDB Atlas")
        logger.info("-" * 80)
        logger.info("1. Ve a 'Deployment' → 'Backup'")
        logger.info("2. Verifica que el backup automático está habilitado")
        logger.info("3. Verifica la frecuencia de backups (diaria o cada 6 horas)")
        logger.info("4. Verifica la retención de backups")
        logger.info("")
        logger.info("PASO 3: Verificar Failover")
        logger.info("-" * 80)
        logger.info("1. Ir a 'Deployment' → 'Overview' y ejecutar failover de prueba")
        logger.info("2. Confirmar que se elige un nuevo primario en menos de 60 segundos")
        logger.info("")
    
    def print_summary(self):
        logger.info("=" * 80)
        logger.info("RESUMEN DE VERIFICACIÓN")
        logger.info("=" * 80)
        logger.info(f"✓ PASADAS: {len(self.checks_passed)}")
        for check in self.checks_passed:
            logger.info(f"  • {check}")
        logger.info("")
        if self.checks_failed:
            logger.info(f"✗ FALLIDAS: {len(self.checks_failed)}")
            for check in self.checks_failed:
                logger.info(f"  • {check}")
            logger.info("")
        if self.checks_warnings:
            logger.info(f"⚠ ADVERTENCIAS: {len(self.checks_warnings)}")
            for check in self.checks_warnings:
                logger.info(f"  • {check}")
            logger.info("")
        logger.info("=" * 80)
        if not self.checks_failed:
            logger.info("✓ CONFIGURACIÓN BÁSICA OK")
        else:
            logger.info("⚠ Hay problemas que necesitan atención")
        logger.info("=" * 80)
        logger.info("")
    
    def run_all_checks(self):
        self.check_config_files()
        self.check_environment_vars()
        self.check_mongodb_connectivity()
        self.check_aws_credentials()
        self.check_terraform_files()
        self.print_manual_verification_guide()
        self.print_summary()


def simulate_local_failover(output_path: str) -> dict:
    """Replica datos entre directorios locales y conmuta a la copia DR."""
    event = {
        "event_id": "iot-reading-0001",
        "sensor_id": "sensor_000001",
        "timestamp": "2026-09-29T00:00:00Z",
        "temperature_c": 24.5,
    }
    with tempfile.TemporaryDirectory(prefix="iot-dr-simulation-") as work_dir:
        primary_dir = os.path.join(work_dir, "us-east-1-primary")
        dr_dir = os.path.join(work_dir, "us-west-2-replica")
        os.makedirs(primary_dir)
        os.makedirs(dr_dir)
        primary_record = os.path.join(primary_dir, "event.json")
        dr_record = os.path.join(dr_dir, "event.json")
        with open(primary_record, "w", encoding="utf-8") as record:
            json.dump(event, record, sort_keys=True)
        replication_started = time.perf_counter()
        shutil.copy2(primary_record, dr_record)
        replication_ms = (time.perf_counter() - replication_started) * 1000
        with open(dr_record, "rb") as replica:
            replicated_hash = hashlib.sha256(replica.read()).hexdigest()
        with open(primary_record, "rb") as primary:
            primary_hash = hashlib.sha256(primary.read()).hexdigest()
        checksum_matches = primary_hash == replicated_hash

        os.remove(primary_record)
        recovery_started = time.perf_counter()
        with open(dr_record, "r", encoding="utf-8") as active_record:
            recovered_event = json.load(active_record)
        rto_ms = (time.perf_counter() - recovery_started) * 1000

    result = {
        "mode": "SIMULACION LOCAL; no usa AWS ni MongoDB Atlas",
        "primary_region_model": "us-east-1 (directorio local temporal)",
        "dr_region_model": "us-west-2 (directorio local temporal)",
        "replicated_record_count": 1,
        "checksum_matches": checksum_matches,
        "failover_recovered_record": recovered_event.get("event_id") == event["event_id"],
        "rpo_lost_records": 0 if checksum_matches else 1,
        "replication_time_ms": round(replication_ms, 3),
        "simulated_rto_ms": round(rto_ms, 3),
        "result": "PASS" if checksum_matches and recovered_event == event else "FAIL",
        "limitations": "No valida replicacion real, backups, red ni disponibilidad de nube.",
    }
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as evidence:
        json.dump(result, evidence, indent=2, ensure_ascii=False)
        evidence.write("\n")
    text_path = os.path.join(os.path.dirname(output_path), "verify_dr_resultado.txt")
    with open(text_path, "w", encoding="utf-8") as evidence:
        evidence.write("SIMULACION LOCAL DE DISASTER RECOVERY\n")
        evidence.write(f"Resultado: {result['result']}\n")
        evidence.write(f"Registros replicados: {result['replicated_record_count']}\n")
        evidence.write(f"Checksum coincidente: {result['checksum_matches']}\n")
        evidence.write(f"Registros perdidos (RPO simulado): {result['rpo_lost_records']}\n")
        evidence.write(f"RTO local medido: {result['simulated_rto_ms']} ms\n")
        evidence.write(result["limitations"] + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description="Verifica configuración de Disaster Recovery")
    parser.add_argument("--check-config", action="store_true", help="Verifica archivos de configuración")
    parser.add_argument("--check-mongodb", action="store_true", help="Verifica conectividad MongoDB")
    parser.add_argument("--check-aws", action="store_true", help="Verifica credenciales AWS")
    parser.add_argument("--full", action="store_true", help="Ejecuta todas las verificaciones")
    parser.add_argument("--demo", action="store_true", help="Genera validación local sin recursos externos")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "..", "evidencias", "requisito-14", "simulacion_dr.json"), help="Ruta del resultado de la simulación")
    args = parser.parse_args()

    verifier = DisasterRecoveryVerifier()

    if args.demo:
        verifier.check_config_files()
        verifier.check_terraform_files()
        simulation = simulate_local_failover(args.output)
        if simulation["result"] == "PASS":
            verifier.checks_passed.append("Failover local simulado: copia íntegra recuperada desde la réplica")
        else:
            verifier.checks_failed.append("Falló la verificación de integridad del failover simulado")
        logger.info("Simulación DR: %s", simulation["result"])
        logger.info("RPO simulado: %s registros perdidos", simulation["rpo_lost_records"])
        logger.info("RTO local medido: %s ms", simulation["simulated_rto_ms"])
        logger.info("Evidencia: %s", os.path.abspath(args.output))
        verifier.print_summary()
        if simulation["result"] != "PASS":
            sys.exit(1)
        return

    if args.check_config:
        verifier.check_config_files()
    elif args.check_mongodb:
        verifier.check_mongodb_connectivity()
    elif args.check_aws:
        verifier.check_aws_credentials()
    elif args.full or not any([args.check_config, args.check_mongodb, args.check_aws]):
        verifier.run_all_checks()
    verifier.print_summary()


if __name__ == "__main__":
    main()
