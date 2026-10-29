#!/usr/bin/env python
"""Script de instalación de dependencias FASE 3"""
import subprocess
import sys

packages = [
    'pymongo>=4.7.0',
    'matplotlib>=3.9.0',
    'pandas>=2.2.0',
    'numpy>=2.0.0',
    'boto3>=1.35.0',
    'faker>=24.0.0',
    'python-dotenv>=1.0.0',
    'click>=8.1.7',
    'tqdm>=4.66.1',
    'pytz>=2024.1'
]

print("=" * 70)
print("FASE 3: INSTALACIÓN DE DEPENDENCIAS PYTHON")
print("=" * 70)
print()

print("📦 Instalando packages...")
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--upgrade'] + packages,
    capture_output=False
)

if result.returncode == 0:
    print()
    print("✓ Instalación completada exitosamente")
    print()
    print("Verificando imports...")
    try:
        import pymongo
        print(f"  ✓ PyMongo {pymongo.__version__}")
        import matplotlib
        print(f"  ✓ Matplotlib {matplotlib.__version__}")
        import pandas
        print(f"  ✓ Pandas {pandas.__version__}")
        import numpy
        print(f"  ✓ NumPy {numpy.__version__}")
        import boto3
        print(f"  ✓ Boto3 {boto3.__version__}")
        from faker import Faker
        print(f"  ✓ Faker")
        from dotenv import load_dotenv
        print(f"  ✓ python-dotenv")
        print()
        print("✓ TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE")
    except ImportError as e:
        print(f"✗ Error importando: {e}")
        sys.exit(1)
else:
    print("✗ Error en la instalación")
    sys.exit(1)
