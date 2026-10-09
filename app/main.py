"""Punto de entrada de la API Taller 2.

Monta los routers de sensores, sensor_magnitudes y mediciones y, mediante el
lifespan, arranca y detiene el consumidor MQTT en el mismo proceso.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import medicion, sensor, sensor_magnitud
from app.mqtt.client import ConsumidorMqtt


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumidor = ConsumidorMqtt()
    consumidor.iniciar()
    yield
    consumidor.detener()


app = FastAPI(title="Taller 2 — API IoT", lifespan=lifespan)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)
