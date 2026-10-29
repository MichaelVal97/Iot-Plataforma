#!/usr/bin/env python3
"""Genera el catálogo de datos de las colecciones IoT en JSON y Markdown."""

import argparse
import json
import os


CATALOG = {
    "database": "iot_platform",
    "mode": "catalogo del esquema de referencia; no requiere acceso a MongoDB",
    "collections": [
        {
            "name": "sensor_readings",
            "description": "Lecturas temporales generadas por sensores IoT.",
            "fields": [
                {"name": "_id", "type": "ObjectId", "required": True, "description": "Identificador generado por MongoDB."},
                {"name": "sensor_id", "type": "string", "required": True, "description": "Identificador del sensor que produjo la lectura."},
                {"name": "timestamp", "type": "datetime", "required": True, "description": "Fecha y hora de la lectura."},
                {"name": "tipo_sensor", "type": "string", "required": True, "description": "Tipo de sensor, por ejemplo weather o temperature."},
                {"name": "temperatura", "type": "number", "required": True, "description": "Temperatura en grados Celsius."},
                {"name": "humedad", "type": "number", "required": True, "description": "Humedad relativa en porcentaje."},
                {"name": "presion", "type": "number", "required": True, "description": "Presión atmosférica en hPa."},
                {"name": "calidad_aire", "type": "integer", "required": True, "description": "Índice de calidad del aire (AQI)."},
                {"name": "energia", "type": "number", "required": True, "description": "Lectura de energía en kW."},
                {"name": "estado", "type": "string", "required": True, "description": "Estado: normal, warning, error o maintenance."},
                {"name": "ubicacion.lat", "type": "number", "required": True, "description": "Latitud geográfica."},
                {"name": "ubicacion.lon", "type": "number", "required": True, "description": "Longitud geográfica."},
                {"name": "datos_adicionales.velocidad_viento", "type": "number", "required": True, "description": "Velocidad del viento simulada."},
                {"name": "datos_adicionales.radiacion_solar", "type": "number", "required": True, "description": "Radiación solar simulada."},
                {"name": "datos_adicionales.precipitacion", "type": "number", "required": True, "description": "Precipitación simulada."},
                {"name": "confiabilidad", "type": "number", "required": True, "description": "Confiabilidad estimada de la lectura, entre 0.8 y 1.0."},
            ],
        },
        {
            "name": "sensors",
            "description": "Metadatos de los sensores registrados en la plataforma.",
            "fields": [
                {"name": "_id", "type": "ObjectId", "required": True, "description": "Identificador generado por MongoDB."},
                {"name": "sensor_id", "type": "string", "required": True, "description": "Identificador único del sensor."},
                {"name": "tipo_sensor", "type": "string", "required": True, "description": "Categoría del sensor."},
                {"name": "ubicacion.lat", "type": "number", "required": True, "description": "Latitud geográfica."},
                {"name": "ubicacion.lon", "type": "number", "required": True, "description": "Longitud geográfica."},
                {"name": "ubicacion.ciudad", "type": "string", "required": True, "description": "Ciudad de instalación."},
                {"name": "ubicacion.pais", "type": "string", "required": True, "description": "País de instalación."},
                {"name": "estado", "type": "string", "required": True, "description": "Estado operativo del sensor; inicialmente activo."},
                {"name": "fecha_instalacion", "type": "datetime", "required": True, "description": "Fecha de instalación."},
                {"name": "fabricante", "type": "string", "required": True, "description": "Fabricante del sensor."},
                {"name": "modelo", "type": "string", "required": True, "description": "Modelo del sensor."},
                {"name": "ultima_calibracion", "type": "datetime", "required": True, "description": "Fecha de la última calibración."},
            ],
        },
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Genera el catálogo de datos IoT")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "evidencias", "requisito-17"),
        help="Directorio para los archivos generados",
    )
    args = parser.parse_args()
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "catalogo_datos.json")
    markdown_path = os.path.join(output_dir, "catalogo_datos.md")
    with open(json_path, "w", encoding="utf-8") as output:
        json.dump(CATALOG, output, indent=2, ensure_ascii=False)
        output.write("\n")

    lines = ["# Catálogo de Datos IoT", "", f"Base de datos: `{CATALOG['database']}`", "", CATALOG["mode"], ""]
    for collection in CATALOG["collections"]:
        lines.extend([
            f"## Colección `{collection['name']}`",
            "",
            collection["description"],
            "",
            "| Campo | Tipo | Obligatorio | Descripción |",
            "|---|---|---|---|",
        ])
        for field in collection["fields"]:
            description = field["description"].replace("|", "\\|")
            lines.append(
                f"| `{field['name']}` | {field['type']} | {'Sí' if field['required'] else 'No'} | {description} |"
            )
        lines.append("")
    with open(markdown_path, "w", encoding="utf-8") as output:
        output.write("\n".join(lines))

    print(f"Catálogo JSON: {json_path}")
    print(f"Catálogo Markdown: {markdown_path}")
    print(f"Colecciones: {len(CATALOG['collections'])}")
    print(f"Campos: {sum(len(collection['fields']) for collection in CATALOG['collections'])}")


if __name__ == "__main__":
    main()