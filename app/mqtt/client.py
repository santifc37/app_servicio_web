"""Consumidor MQTT: recibe, valida y almacena las mediciones del sensor asignado.

Flujo por mensaje (procesar_mensaje):
  1. Decodifica el JSON.
  2. Valida estructura, tipos y timestamp con Pydantic (MedicionPayload).
  3. Consulta con el ORM el sensor (por `codigo`), su estado y la configuración
     de cada magnitud (unidad y rango).
  4. Si TODAS las magnitudes son válidas, inserta una fila por magnitud en
     `mediciones` con el mismo timestamp_utc; si alguna falla, no guarda nada.

Los mensajes inválidos se rechazan y se registran en el log; nunca detienen el
consumidor. Los códigos HTTP no aplican aquí (solo a los endpoints FastAPI).
"""

import json
import logging
import os
from datetime import timezone
from decimal import Decimal
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import SessionLocal
from app.models.medicion import Medicion
from app.schemas.medicion import MedicionPayload

load_dotenv()

logger = logging.getLogger("mqtt")

RUTA_LOG = Path(os.getenv("MQTT_LOG_FILE", "evidencias/registro_mqtt.txt"))


class MensajeRechazado(Exception):
    """El mensaje no supera alguna validación y no se almacena."""


def configurar_log() -> None:
    """Envía el log del consumidor a consola y al archivo de evidencias."""
    if logger.handlers:
        return
    formato = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    logger.setLevel(logging.INFO)
    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    logger.addHandler(consola)
    try:
        RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
        archivo = logging.FileHandler(RUTA_LOG, encoding="utf-8")
        archivo.setFormatter(formato)
        logger.addHandler(archivo)
    except OSError as error:  # el log en archivo es opcional
        logger.warning("No se pudo abrir el archivo de log %s: %s", RUTA_LOG, error)


def validar_payload(crudo: bytes | str) -> MedicionPayload:
    """Decodifica y valida la estructura del mensaje (solo Pydantic)."""
    try:
        datos = json.loads(crudo)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MensajeRechazado(f"JSON inválido: {error}") from error
    try:
        return MedicionPayload.model_validate(datos)
    except ValidationError as error:
        detalle = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()
        )
        raise MensajeRechazado(f"Estructura/tipos/timestamp inválidos: {detalle}") from error


def construir_mediciones(db: Session, payload: MedicionPayload) -> list[Medicion]:
    """Valida contra el catálogo (ORM) y devuelve las filas a insertar.

    Lanza MensajeRechazado si el sensor no existe o está inactivo, o si alguna
    magnitud no está asociada al sensor, tiene otra unidad o sale de rango.
    """
    sensor = crud_sensor.get_sensor_por_codigo(db, payload.sensor_id)
    if sensor is None:
        raise MensajeRechazado(f"Sensor inexistente: '{payload.sensor_id}'")
    if not sensor.activo:
        raise MensajeRechazado(f"Sensor inactivo: '{sensor.codigo}'")

    timestamp_utc = payload.timestamp.astimezone(timezone.utc)
    filas: list[Medicion] = []
    for nombre, item in payload.measurements.items():
        config = crud_sensor_magnitud.get_magnitud_config(db, sensor.id, nombre)
        if config is None:
            raise MensajeRechazado(
                f"Magnitud '{nombre}' no pertenece al sensor '{sensor.codigo}'"
            )
        if item.unit != config.unidad:
            raise MensajeRechazado(
                f"Unidad incorrecta en '{nombre}': recibida '{item.unit}', "
                f"esperada '{config.unidad}'"
            )
        valor = Decimal(str(item.value))
        if not (config.valor_minimo <= valor <= config.valor_maximo):
            raise MensajeRechazado(
                f"Valor fuera de rango en '{nombre}': {valor} no está en "
                f"[{config.valor_minimo}, {config.valor_maximo}]"
            )
        filas.append(
            Medicion(
                sensor_magnitud_id=config.id,
                valor=valor,
                timestamp_utc=timestamp_utc,
            )
        )
    return filas


def procesar_mensaje(db: Session, crudo: bytes | str) -> list[Medicion]:
    """Valida y almacena un mensaje; devuelve las filas guardadas.

    Lanza MensajeRechazado si no pasa las validaciones (no se guarda nada).
    """
    payload = validar_payload(crudo)
    filas = construir_mediciones(db, payload)
    crud_medicion.insertar_mediciones(db, filas)  # una sola transacción
    return filas


class ConsumidorMqtt:
    """Suscriptor MQTT que corre en un hilo propio (loop_start de paho)."""

    def __init__(self) -> None:
        self.broker = os.getenv("MQTT_BROKER")
        self.puerto = int(os.getenv("MQTT_PORT", "1883"))
        self.topico = os.getenv("MQTT_TOPIC")
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        usuario = os.getenv("MQTT_USERNAME")
        if usuario:
            self.cliente.username_pw_set(usuario, os.getenv("MQTT_PASSWORD") or "")
        self.cliente.on_connect = self._on_connect
        self.cliente.on_message = self._on_message
        self.cliente.reconnect_delay_set(min_delay=1, max_delay=30)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            logger.error("Error de conexión MQTT: %s", reason_code)
            return
        client.subscribe(self.topico)
        logger.info("Conectado a %s:%s y suscrito a %s", self.broker, self.puerto, self.topico)

    def _on_message(self, client, userdata, mensaje):
        crudo = mensaje.payload
        logger.info("RECIBIDO %s: %s", mensaje.topic, crudo.decode("utf-8", "replace"))
        db = SessionLocal()
        try:
            filas = procesar_mensaje(db, crudo)
            logger.info(
                "ALMACENADO %d medición(es): %s",
                len(filas),
                ", ".join(f"mag_id={f.sensor_magnitud_id} valor={f.valor}" for f in filas),
            )
        except MensajeRechazado as motivo:
            logger.warning("RECHAZADO: %s", motivo)
        except Exception:  # un fallo (p. ej. BD) no debe tumbar el consumidor
            logger.exception("ERROR INTERNO procesando el mensaje")
        finally:
            db.close()

    def iniciar(self) -> None:
        if not self.broker or not self.topico:
            raise RuntimeError("Faltan MQTT_BROKER o MQTT_TOPIC en el archivo .env")
        configurar_log()
        self.cliente.connect_async(self.broker, self.puerto, self.keepalive)
        self.cliente.loop_start()

    def detener(self) -> None:
        self.cliente.loop_stop()
        self.cliente.disconnect()
        logger.info("Consumidor MQTT detenido")
