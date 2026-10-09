"""Pruebas del procesamiento MQTT (evidencias 2-7)."""

import json

import pytest

from app.models.medicion import Medicion
from app.mqtt.client import MensajeRechazado, procesar_mensaje


def msg(**cambios):
    base = {
        "sensor_id": "ENV-003",
        "timestamp": "2026-10-09T14:00:00Z",
        "measurements": {
            "temperature": {"value": 24.6, "unit": "C"},
            "humidity": {"value": 55, "unit": "%"},
        },
    }
    base.update(cambios)
    return json.dumps(base)


def total(db):
    return db.query(Medicion).count()


def test_valido_guarda_una_fila_por_magnitud_con_mismo_timestamp(db):
    filas = procesar_mensaje(db, msg())
    assert len(filas) == 2 and total(db) == 2
    assert len({f.timestamp_utc for f in filas}) == 1


@pytest.mark.parametrize("crudo,motivo", [
    (msg(sensor_id="NOPE-999"), "inexistente"),
    (msg(sensor_id="OFF-001", measurements={"pm25": {"value": 5, "unit": "ug/m3"}}), "inactivo"),
    (msg(measurements={"temperature": {"value": 24.6, "unit": "F"}}), "Unidad"),
    (msg(measurements={"temperature": {"value": "24.6", "unit": "C"}}), "inválidos"),
    (msg(measurements={"temperature": {"value": True, "unit": "C"}}), "inválidos"),
    (msg(measurements={"co2": {"value": 400, "unit": "ppm"}}), "Magnitud"),
    (msg(timestamp="ayer"), "inválidos"),
    (msg(timestamp="2026-10-09T14:00:00"), "inválidos"),  # sin zona horaria
    (msg(timestamp=1760000000), "inválidos"),
    (msg(measurements={"temperature": {"value": 999, "unit": "C"}}), "rango"),
    (msg(measurements={}), "inválidos"),
    ("no es json", "JSON"),
])
def test_invalidos_se_rechazan_y_no_se_guardan(db, crudo, motivo):
    with pytest.raises(MensajeRechazado, match=motivo):
        procesar_mensaje(db, crudo)
    assert total(db) == 0


def test_todo_o_nada_si_una_magnitud_es_invalida(db):
    crudo = msg(measurements={
        "temperature": {"value": 24.6, "unit": "C"},
        "humidity": {"value": 55, "unit": "X"},
    })
    with pytest.raises(MensajeRechazado):
        procesar_mensaje(db, crudo)
    assert total(db) == 0
