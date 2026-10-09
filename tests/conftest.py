"""Fixtures: BD SQLite en memoria con un catálogo mínimo para el sensor ENV-003."""

import os
import sys
from decimal import Decimal
from pathlib import Path

for k, v in dict(DB_HOST="x", DB_PORT="1", DB_NAME="x", DB_USER="x", DB_PASSWORD="x").items():
    os.environ.setdefault(k, v)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models.medicion import Medicion
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Medicion.__table__.c.id.type = Integer()  # SQLite no autoincrementa BIGINT
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine, expire_on_commit=False)()
    s = Sensor(codigo="ENV-003", nombre="Ambiental", categoria="AMBIENTE",
               ubicacion="Lab", activo=True)
    inactivo = Sensor(codigo="OFF-001", nombre="Apagado", categoria="AIRE",
                      ubicacion="Lab", activo=False)
    sesion.add_all([s, inactivo])
    sesion.flush()
    sesion.add_all([
        SensorMagnitud(sensor_id=s.id, magnitud="temperature", unidad="C",
                       valor_minimo=Decimal("-10"), valor_maximo=Decimal("50")),
        SensorMagnitud(sensor_id=s.id, magnitud="humidity", unidad="%",
                       valor_minimo=Decimal("0"), valor_maximo=Decimal("100")),
        SensorMagnitud(sensor_id=inactivo.id, magnitud="pm25", unidad="ug/m3",
                       valor_minimo=Decimal("0"), valor_maximo=Decimal("500")),
    ])
    sesion.commit()
    yield sesion
    sesion.close()
