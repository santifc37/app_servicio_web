import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from integrador import normalizar_registro, validar_localmente

def test_transformacion_correcta():
    raw_b = {
        "_origen_raw": "proveedor_b",
        "_trazabilidad_id": "proveedor_b_1",
        "municipality": "Medellin",
        "country": "CO",
        "latitude_deg": "6.2442",
        "longitude_deg": "-75.5812",
        "temp_celsius": "22.5",
        "humidity_pct": "60.0",
        "wind_kmh": "15.0",
        "measurement_time": "01/09/2026 14:30"
    }
    norm, err = normalizar_registro(raw_b)
    assert err is None
    assert norm["ciudad"] == "Medellin"
    assert norm["fecha_hora"] == "2026-09-01T14:30:00"

def test_conversion_unidades():
    raw_a = {
        "_origen_raw": "proveedor_a",
        "_trazabilidad_id": "proveedor_a_1",
        "station": {"city_name": "Bogota", "country_code": "CO"},
        "location": {"lat": 4.6097, "lon": -74.0817},
        "measurements": {
            "temperature_f": 68.0,
            "relative_humidity": 50.0,
            "wind_speed_ms": 10.0
        },
        "observed_at": "2026-09-01T10:00:00-05:00"
    }
    norm, err = normalizar_registro(raw_a)
    assert norm["temperatura_c"] == 20.0
    assert norm["viento_kmh"] == 36.0

def test_registro_valido():
    norm_valido = {
        "ciudad": "Cali",
        "pais": "CO",
        "latitud": 3.4516,
        "longitud": -76.5320,
        "temperatura_c": 25.0,
        "humedad": 70.0,
        "viento_kmh": 12.0,
        "fecha_hora": "2026-09-01T12:00:00",
        "origen": "proveedor_a"
    }
    assert validar_localmente(norm_valido) is True

def test_registro_invalido():
    norm_invalido = {
        "ciudad": "Barranquilla",
        "pais": "CO",
        "latitud": 10.9685,
        "longitud": -74.7813,
        "temperatura_c": 30.0,
        "humedad": 150.0,
        "viento_kmh": 10.0,
        "fecha_hora": "2026-09-01T12:00:00",
        "origen": "proveedor_a"
    }
    assert validar_localmente(norm_invalido) is False

def test_caso_limite_latitud_borde():
    norm_limite = {
        "ciudad": "Polo Norte",
        "pais": "XX",
        "latitud": 90.0,
        "longitud": -180.0,
        "temperatura_c": -10.0,
        "humedad": 0.0,
        "viento_kmh": 0.0,
        "fecha_hora": "2026-09-01T00:00:00",
        "origen": "proveedor_b"
    }
    assert validar_localmente(norm_limite) is True