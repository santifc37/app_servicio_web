"""Pruebas de los endpoints (evidencias 8-16 y códigos 200/400/404/422)."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import medicion, sensor, sensor_magnitud
from app.database.connection import get_db
from app.mqtt.client import procesar_mensaje


@pytest.fixture()
def cliente(db):
    app = FastAPI()
    for r in (sensor.router, sensor_magnitud.router, medicion.router):
        app.include_router(r)
    app.dependency_overrides[get_db] = lambda: db
    for i, ts in enumerate(["14:00:00", "14:01:00", "14:02:00"]):
        procesar_mensaje(db, json.dumps({
            "sensor_id": "ENV-003", "timestamp": f"2026-10-09T{ts}Z",
            "measurements": {"temperature": {"value": 20 + i, "unit": "C"},
                             "humidity": {"value": 50 + i, "unit": "%"}}}))
    return TestClient(app)


def test_sensores_y_codigo(cliente):
    assert cliente.get("/sensores").status_code == 200
    r = cliente.get("/sensores/por-codigo/ENV-003")
    assert r.status_code == 200 and r.json()["codigo"] == "ENV-003"
    assert cliente.get("/sensores/por-codigo/XXX").status_code == 404


def test_magnitudes(cliente):
    sid = cliente.get("/sensores/por-codigo/ENV-003").json()["id"]
    mags = cliente.get(f"/sensores/{sid}/magnitudes").json()
    assert {m["magnitud"] for m in mags} == {"temperature", "humidity"}
    assert cliente.get(f"/sensor-magnitudes/{mags[0]['id']}").status_code == 200
    assert cliente.get("/sensor-magnitudes/9999").status_code == 404


def test_medicion_por_id_y_hora_colombia(cliente):
    r = cliente.get("/mediciones/1")
    assert r.status_code == 200
    assert r.json()["timestamp_local"] == "2026-10-09 09:00:00"  # UTC-5
    assert cliente.get("/mediciones/99999").status_code == 404


def test_historico_filtros_y_limit(cliente):
    sid = cliente.get("/sensores/por-codigo/ENV-003").json()["id"]
    base = f"/sensores/{sid}/mediciones"
    assert len(cliente.get(base).json()) == 6
    assert len(cliente.get(base, params={"limit": 2}).json()) == 2
    temp = cliente.get(base, params={"magnitud": "temperature"}).json()
    assert len(temp) == 3
    rango = cliente.get(base, params={"desde": "2026-10-09T14:01:00Z",
                                      "hasta": "2026-10-09T14:01:30Z"}).json()
    assert len(rango) == 2
    combo = cliente.get(base, params={"magnitud": "temperature", "limit": 1}).json()
    assert combo[0]["valor"] == "22.0000" or float(combo[0]["valor"]) == 22.0


def test_errores_http(cliente):
    sid = cliente.get("/sensores/por-codigo/ENV-003").json()["id"]
    r = cliente.get(f"/sensores/{sid}/mediciones",
                    params={"desde": "2026-10-10T00:00:00Z", "hasta": "2026-10-09T00:00:00Z"})
    assert r.status_code == 400
    assert cliente.get(f"/sensores/{sid}/mediciones", params={"limit": "abc"}).status_code == 422
    assert cliente.get("/sensores/abc").status_code == 422
    assert cliente.get("/sensores/9999/mediciones").status_code == 404


def test_ultima_medicion(cliente):
    sid = cliente.get("/sensores/por-codigo/ENV-003").json()["id"]
    r = cliente.get(f"/sensores/{sid}/ultima-medicion")
    assert r.status_code == 200 and r.json()["timestamp_local"] == "2026-10-09 09:02:00"
