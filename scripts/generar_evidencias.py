
"""Genera evidencias/pruebas.md contra la base de datos real.

Uso desde la raíz del repositorio:
    python scripts/generar_evidencias.py

Pruebas:
    1: Recepción MQTT a partir del registro de ejecución.
    2: Mediciones existentes en PostgreSQL para el sensor asignado.
    3-7: Rechazo de payloads MQTT inválidos y comprobación de no inserción.
    8-16: Consultas y validaciones de la API FastAPI.
    17: Comprobación de relaciones mediante claves foráneas.
    18: Separación de responsabilidades del proyecto.

El script no crea mediciones artificiales en PostgreSQL.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.main import app
from app.models.medicion import Medicion
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud
from app.mqtt.client import MensajeRechazado, procesar_mensaje


CODIGO = "ENV-003"
SALIDA = Path("evidencias/pruebas.md")
RUTA_LOG_MQTT = Path("evidencias/registro_mqtt.txt")

out: list[str] = [
    "# Evidencias de pruebas — sensor " + CODIGO,
    f"\nGenerado: {datetime.now(timezone.utc).isoformat()}\n",
]


def seccion(num, titulo, entrada, resultado, ref, nota=""):
    """Añade una prueba al informe Markdown."""
    out.append(f"## {num}. {titulo}\n")
    out.append(f"- **Entrada:** `{entrada}`")
    out.append(f"- **Resultado:**\n\n```\n{resultado}\n```")
    out.append(f"- **Implementación:** {ref}")

    if nota:
        out.append(f"- **Explicación:** {nota}")

    out.append("")


def cortar(texto, n=900):
    """Limita la longitud de las respuestas HTTP incluidas."""
    texto = str(texto)
    return texto if len(texto) <= n else texto[:n] + "\n... (recortado)"



db = SessionLocal()


def total_mediciones():
    """Devuelve el total actual de registros en mediciones."""
    return db.scalar(select(func.count()).select_from(Medicion))


try:
    # ================================================================
    # PRUEBA 1: RECEPCIÓN MQTT
    # ================================================================

    if RUTA_LOG_MQTT.exists():
        contenido_log = RUTA_LOG_MQTT.read_text(
            encoding="utf-8",
            errors="replace",
        )

        # El cliente registra:
        # RECIBIDO <tópico>: <payload>
        # ALMACENADO <cantidad> medición(es): ...
        lineas_mqtt = [
            linea
            for linea in contenido_log.splitlines()
            if CODIGO in linea
            and any(
                palabra in linea.lower()
                for palabra in (
                    "recibido",
                    "almacenado",
                    "suscrito",
                )
            )
        ]

        if lineas_mqtt:
            resultado_mqtt = (
                f"Registros encontrados para {CODIGO}:\n"
                + "\n".join(lineas_mqtt[-10:])
            )
        else:
            resultado_mqtt = (
                f"NO VERIFICADO: el archivo existe, pero no se encontraron "
                f"registros identificables de recepción o almacenamiento "
                f"para {CODIGO}.\n"
                f"Archivo consultado: {RUTA_LOG_MQTT}"
            )
    else:
        resultado_mqtt = (
            "NO VERIFICADO: no se encontró el archivo de registro MQTT.\n"
            f"Archivo esperado: {RUTA_LOG_MQTT}\n"
            "Inicia el consumidor MQTT y conserva su registro de ejecución."
        )

    seccion(
        1,
        "Recepción MQTT",
        f"Mensajes del tópico asignado al sensor {CODIGO}",
        resultado_mqtt,
        "`app/mqtt/client.py` — `ConsumidorMqtt._on_message`",
        "Se consulta el registro de ejecución existente. "
        "La ausencia de registros no se considera una prueba superada.",
    )

    # ================================================================
    # PRUEBA 2: MEDICIÓN VÁLIDA ALMACENADA EN POSTGRESQL
    # ================================================================

    # Los modelos no definen relaciones ORM entre sí, por lo que se
    # realizan las uniones explícitamente usando las claves foráneas.
    filas_validas = db.execute(
        select(
            Medicion.id,
            Sensor.codigo,
            SensorMagnitud.magnitud,
            SensorMagnitud.unidad,
            Medicion.valor,
            Medicion.timestamp_utc,
        )
        .join(
            SensorMagnitud,
            Medicion.sensor_magnitud_id == SensorMagnitud.id,
        )
        .join(
            Sensor,
            SensorMagnitud.sensor_id == Sensor.id,
        )
        .where(Sensor.codigo == CODIGO)
        .order_by(Medicion.timestamp_utc.desc())
        .limit(5)
    ).all()

    if filas_validas:
        resultado_db = (
            f"VERIFICADO: existen mediciones almacenadas para {CODIGO}.\n"
            f"Registros consultados: {len(filas_validas)} "
            "(máximo 5).\n\n"
            "id | sensor | magnitud | unidad | valor | timestamp_utc\n"
            + "\n".join(str(fila) for fila in filas_validas)
        )
    else:
        resultado_db = (
            f"NO VERIFICADO: no se encontraron mediciones almacenadas "
            f"para el sensor {CODIGO} en PostgreSQL."
        )

    seccion(
        2,
        "Medición válida almacenada en PostgreSQL",
        f"Consultar las últimas 5 mediciones de {CODIGO}",
        resultado_db,
        "`app/crud/medicion.py` — `insertar_mediciones`; "
        "`app/models/medicion.py` — modelo `Medicion`",
        "Se consultan registros reales de PostgreSQL mediante las "
        "claves foráneas. No se insertan datos artificiales.",
    )

    # ================================================================
    # PRUEBAS 3-7: RECHAZOS MQTT
    # ================================================================

    base = {
        "sensor_id": CODIGO,
        "timestamp": "2026-10-09T14:00:00Z",
        "measurements": {
            "wind_speed": {
                "value": 12.5,
                "unit": "m/s",
            }
        },
    }

    casos = [
        (
            3,
            "Sensor inexistente",
            {**base, "sensor_id": "NOPE-999"},
        ),
        (
            4,
            "Unidad incorrecta",
            {
                **base,
                "measurements": {
                    "wind_speed": {
                        "value": 12.5,
                        "unit": "km/h",
                    }
                },
            },
        ),
        (
            5,
            "Tipo de dato incorrecto",
            {
                **base,
                "measurements": {
                    "wind_speed": {
                        "value": "caliente",
                        "unit": "m/s",
                    }
                },
            },
        ),
        (
            6,
            "Magnitud incorrecta",
            {
                **base,
                "measurements": {
                    "magnitud_falsa": {
                        "value": 1,
                        "unit": "m/s",
                    }
                },
            },
        ),
        (
            7,
            "Timestamp inválido",
            {**base, "timestamp": "no-es-fecha"},
        ),
    ]

    for num, titulo, payload in casos:
        antes = total_mediciones()

        try:
            procesar_mensaje(db, json.dumps(payload))
            res = (
                "ACEPTADO: el mensaje no fue rechazado. "
                "Revisar la validación."
            )
        except MensajeRechazado as motivo:
            res = f"RECHAZADO correctamente: {motivo}"
        except Exception as error:
            res = (
                f"ERROR INESPERADO: {type(error).__name__}: {error}\n"
                "Esta excepción no se considera una validación superada."
            )

        despues = total_mediciones()

        if antes == despues:
            res += (
                f"\nmediciones antes={antes}, después={despues}"
                "\nNo hubo cambios en el total de mediciones."
            )
        else:
            res += (
                f"\nERROR: mediciones antes={antes}, después={despues}"
                "\nEl total cambió durante la prueba."
            )

        seccion(
            num,
            titulo,
            json.dumps(payload, ensure_ascii=False),
            res,
            "`app/mqtt/client.py` — `validar_payload` / "
            "`construir_mediciones`",
            "Se comprueba el rechazo y se compara el total de filas "
            "antes y después.",
        )

    # ================================================================
    # PRUEBAS 8-16: API FASTAPI
    # ================================================================

    # No usar "with TestClient(app)" para evitar iniciar el consumidor
    # MQTT durante la generación de evidencias.
    c = TestClient(app)

    respuesta_sensor = c.get(f"/sensores/por-codigo/{CODIGO}")

    if respuesta_sensor.status_code != 200:
        raise RuntimeError(
            f"No se pudo consultar el sensor {CODIGO}: "
            f"HTTP {respuesta_sensor.status_code}. "
            "Comprueba la conexión y los datos de PostgreSQL."
        )

    sensor = respuesta_sensor.json()
    sid = sensor["id"]

    ref_api = "`app/api/medicion.py` / `app/crud/medicion.py`"

    def get(ruta, **params):
        """Ejecuta una consulta y prepara su resultado para el informe."""
        r = c.get(ruta, params=params)
        try:
            cuerpo = json.dumps(
                r.json(),
                indent=2,
                ensure_ascii=False,
            )
        except ValueError:
            cuerpo = r.text

        return r, f"HTTP {r.status_code}\n{cortar(cuerpo)}"

    # 8. Consulta por ID existente
    primero = db.scalars(
        select(Medicion).order_by(Medicion.id).limit(1)
    ).first()

    if primero:
        id_existente = primero.id
        ruta = f"/mediciones/{id_existente}"
        _, resultado = get(ruta)
    else:
        id_existente = None
        ruta = "/mediciones/1"
        _, resultado = get(ruta)
        resultado = (
            "NO VERIFICADO: no existen mediciones para seleccionar "
            "un ID existente.\n" + resultado
        )

    seccion(
        8,
        "Consulta por ID existente",
        f"GET {ruta}",
        resultado,
        f"{ref_api} — `obtener_medicion`",
        "La respuesta de una medición incluye timestamp UTC y hora local.",
    )

    # 9. Consulta por ID inexistente
    _, resultado = get("/mediciones/999999999")

    seccion(
        9,
        "Consulta por ID inexistente",
        "GET /mediciones/999999999",
        resultado,
        f"{ref_api} — `obtener_medicion`",
        "Se espera HTTP 404.",
    )

    # 10. Consulta histórica
    _, resultado = get(
        f"/sensores/{sid}/mediciones",
        limit=5,
    )

    seccion(
        10,
        "Consulta histórica",
        f"GET /sensores/{sid}/mediciones?limit=5",
        resultado,
        f"{ref_api} — `listar_mediciones` / `get_mediciones`",
    )

    # 11. Consulta por rango de fechas
    respuesta_ultima = c.get(f"/sensores/{sid}/ultima-medicion")

    if respuesta_ultima.status_code == 200:
        ultima = respuesta_ultima.json()

        if "timestamp_utc" in ultima:
            ts = datetime.fromisoformat(
                ultima["timestamp_utc"].replace("Z", "+00:00")
            )
        else:
            ts = datetime.now(timezone.utc)

        # Evita enviar fechas sin zona horaria a la API.
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        desde = (ts - timedelta(minutes=5)).isoformat()
        hasta = ts.isoformat()

        _, resultado = get(
            f"/sensores/{sid}/mediciones",
            desde=desde,
            hasta=hasta,
        )
    else:
        desde = datetime.now(timezone.utc).isoformat()
        hasta = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        resultado = (
            f"NO VERIFICADO: no se pudo obtener la última medición. "
            f"HTTP {respuesta_ultima.status_code}."
        )

    seccion(
        11,
        "Consulta por rango de fechas",
        f"GET /sensores/{sid}/mediciones?desde={desde}&hasta={hasta}",
        resultado,
        f"{ref_api} — `listar_mediciones`",
        "Consulta el histórico con límites temporales.",
    )

    # 12. Rango desde > hasta
    _, resultado = get(
        f"/sensores/{sid}/mediciones",
        desde=hasta,
        hasta=desde,
    )

    seccion(
        12,
        "Rango desde > hasta",
        f"GET /sensores/{sid}/mediciones?desde={hasta}&hasta={desde}",
        resultado,
        f"{ref_api} — `listar_mediciones`",
        "Se espera HTTP 400.",
    )

    # 13. Parámetro HTTP inválido
    _, resultado = get(
        f"/sensores/{sid}/mediciones",
        limit="abc",
    )

    seccion(
        13,
        "Validación HTTP incorrecta",
        f"GET /sensores/{sid}/mediciones?limit=abc",
        resultado,
        "FastAPI/Pydantic — parámetro `limit`",
        "Se espera HTTP 422.",
    )

    # 14. Última medición
    _, resultado = get(f"/sensores/{sid}/ultima-medicion")

    seccion(
        14,
        "Última medición",
        f"GET /sensores/{sid}/ultima-medicion",
        resultado,
        f"{ref_api} — `obtener_ultima_medicion` / "
        "`get_ultima_medicion`",
    )

    # 15. Últimas N mediciones
    _, resultado = get(
        f"/sensores/{sid}/mediciones",
        limit=3,
    )

    seccion(
        15,
        "Últimas N mediciones",
        f"GET /sensores/{sid}/mediciones?limit=3",
        resultado,
        f"{ref_api} — `get_mediciones`",
        "Comprueba la consulta limitada a tres registros.",
    )

    # 16. Filtro por magnitud
    mags = c.get(f"/sensores/{sid}/magnitudes")

    if mags.status_code == 200 and mags.json():
        mag = mags.json()[0]["magnitud"]

        _, resultado = get(
            f"/sensores/{sid}/mediciones",
            magnitud=mag,
            limit=5,
        )
    else:
        mag = "no disponible"
        resultado = (
            f"NO VERIFICADO: no se pudieron obtener las magnitudes. "
            f"HTTP {mags.status_code}."
        )

    seccion(
        16,
        "Filtro por magnitud",
        f"GET /sensores/{sid}/mediciones?magnitud={mag}&limit=5",
        resultado,
        f"{ref_api} — `_ids_magnitudes_del_sensor`",
    )

    # ================================================================
    # PRUEBA 17: CLAVES FORÁNEAS
    # ================================================================

    filas_fk = db.execute(
        select(
            Medicion.id,
            Medicion.sensor_magnitud_id,
            SensorMagnitud.sensor_id,
            Sensor.codigo,
        )
        .join(
            SensorMagnitud,
            Medicion.sensor_magnitud_id == SensorMagnitud.id,
        )
        .join(
            Sensor,
            SensorMagnitud.sensor_id == Sensor.id,
        )
        .where(Sensor.codigo == CODIGO)
        .order_by(Medicion.id.desc())
        .limit(3)
    ).all()

    if filas_fk:
        resultado_fk = (
            "Últimas filas relacionadas (medicion_id, "
            "sensor_magnitud_id, sensor_id, codigo):\n"
            + "\n".join(str(fila) for fila in filas_fk)
        )
    else:
        resultado_fk = (
            f"NO VERIFICADO: no hay mediciones relacionadas "
            f"con {CODIGO}."
        )

    seccion(
        17,
        "Claves foráneas",
        "mediciones.sensor_magnitud_id -> "
        "sensor_magnitudes.id -> sensores.id",
        resultado_fk,
        "`app/models/medicion.py`, `sensor_magnitud.py`, `sensor.py`",
        "Se consultan las relaciones reales mediante JOIN y las claves "
        "foráneas definidas en los modelos.",
    )

    # ================================================================
    # PRUEBA 18: SEPARACIÓN DE RESPONSABILIDADES
    # ================================================================

    estructura = (
        "schemas/ (Pydantic) · models/ (ORM) · crud/ (consultas) · "
        "api/ (rutas) · mqtt/ (consumidor) · database/ (conexión)"
    )

    seccion(
        18,
        "Separación de responsabilidades",
        "Estructura de app/",
        estructura,
        "README.md, sección 5; estructura de directorios del proyecto",
        "Descripción de la organización modular del código.",
    )

    # ================================================================
    # ESCRITURA DEL INFORME
    # ================================================================

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"Evidencias escritas en {SALIDA.resolve()}")
    print("Secciones generadas: 1 a 18.")
    print("Revisa las secciones marcadas como NO VERIFICADO.")

finally:
    db.close()