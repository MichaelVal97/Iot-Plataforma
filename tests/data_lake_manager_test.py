from collections import defaultdict
from datetime import datetime, timezone

from scripts.data_lake_manager import add_to_daily_summary, finalize_daily_summaries, map_reading


def new_summaries():
    metrics = ("temperatura", "humedad", "presion", "calidad_aire", "energia")
    return defaultdict(
        lambda: {
            "cantidad_lecturas": 0,
            **{
                f"{metric}_{part}": 0
                for metric in metrics
                for part in ("suma", "conteo")
            },
        }
    )


def test_map_reading_flattens_nested_fields_and_normalizes_timestamp():
    timestamp = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    reading = map_reading(
        {
            "_id": "reading-1",
            "sensor_id": "sensor-1",
            "timestamp": timestamp,
            "tipo_sensor": "clima",
            "temperatura": 22.5,
            "ubicacion": {"lat": 4.6, "lon": -74.1},
            "datos_adicionales": {"velocidad_viento": 3.2},
        }
    )

    assert reading["reading_id"] == "reading-1"
    assert reading["timestamp"] == timestamp
    assert reading["lat"] == 4.6
    assert reading["velocidad_viento"] == 3.2


def test_daily_summary_averages_metrics_and_counts_readings():
    summaries = new_summaries()
    for value in (20.0, 22.0):
        reading = {
            "timestamp": datetime(2026, 10, 28, tzinfo=timezone.utc),
            "tipo_sensor": "clima",
            "temperatura": value,
        }
        add_to_daily_summary(summaries, reading)

    [summary] = finalize_daily_summaries(summaries)

    assert summary["fecha"] == "2026-10-28"
    assert summary["tipo_sensor"] == "clima"
    assert summary["cantidad_lecturas"] == 2
    assert summary["temperatura_promedio"] == 21.0
    assert summary["humedad_promedio"] is None