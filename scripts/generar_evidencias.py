"""Genera evidencias/pruebas.md contra la BD real (ejecutar tras recolectar datos).

Uso:  python scripts/generar_evidencias.py
- Pruebas de rechazo (3-7): llama a procesar_mensaje con payloads inválidos y
  comprueba que el conteo de `mediciones` no cambia.
- Pruebas de API (8-16): usa TestClient sobre la app real (sin arrancar MQTT).
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
from app.mqtt.client import MensajeRechazado, procesar_mensaje

CODIGO = "ENV-003"
SALIDA = Path("evidencias/pruebas.md")
out: list[str] = ["# Evidencias de pruebas — sensor " + CODIGO,
                  f"\nGenerado: {datetime.now(timezone.utc).isoformat()}\n"]


def seccion(num, titulo, entrada, resultado, ref, nota=""):
    out.append(f"## {num}. {titulo}\n")
    out.append(f"- **Entrada:** `{entrada}`")
    out.append(f"- **Resultado:**\n\n```\n{resultado}\n```")
    out.append(f"- **Implementación:** {ref}")
    if nota:
        out.append(f"- **Explicación:** {nota}")
    out.append("")


def cortar(texto, n=900):
    texto = str(texto)
    return texto if len(texto) <= n else texto[:n] + "\n... (recortado)"


db = SessionLocal()
total = lambda: db.scalar(select(func.count()).select_from(Medicion))

# ---- Rechazos MQTT (3-7) -------------------------------------------------
base = {"sensor_id": CODIGO, "timestamp": "2026-10-09T14:00:00Z",
        "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}
casos = [
    (3, "Sensor inexistente", {**base, "sensor_id": "NOPE-999"}),
    (4, "Unidad incorrecta", {**base, "measurements": {"wind_speed": {"value": 12.5, "unit": "km/h"}}}),
    (5, "Tipo de dato incorrecto", {**base, "measurements": {"wind_speed": {"value": "caliente", "unit": "m/s"}}}),
    (6, "Magnitud incorrecta", {**base, "measurements": {"magnitud_falsa": {"value": 1, "unit": "m/s"}}}),
    (7, "Timestamp inválido", {**base, "timestamp": "no-es-fecha"}),
]
for num, titulo, payload in casos:
    antes = total()
    try:
        procesar_mensaje(db, json.dumps(payload))
        res = "ACEPTADO (inesperado)"
    except MensajeRechazado as motivo:
        res = f"RECHAZADO: {motivo}"
    despues = total()
    res += f"\nmediciones antes={antes} después={despues} -> {'no almacenado OK' if antes == despues else 'ERROR'}"
    seccion(num, titulo, json.dumps(payload), res,
            "`app/mqtt/client.py` — `validar_payload` / `construir_mediciones`",
            "El mensaje se rechaza y se registra; no se inserta ninguna fila.")

# ---- API (8-16) -----------------------------------------------------------
c = TestClient(app)  # sin 'with': no dispara el lifespan (no arranca MQTT)
sensor = c.get(f"/sensores/por-codigo/{CODIGO}").json()
sid = sensor["id"]
ref_api = "`app/api/medicion.py` / `app/crud/medicion.py`"


def get(ruta, **params):
    r = c.get(ruta, params=params)
    return r, f"HTTP {r.status_code}\n{cortar(json.dumps(r.json(), indent=2, ensure_ascii=False))}"


r, t = get("/mediciones/1")
primero = db.scalars(select(Medicion).order_by(Medicion.id).limit(1)).first()
if primero:
    r, t = get(f"/mediciones/{primero.id}")
seccion(8, "Consulta por ID existente", f"GET /mediciones/{primero.id if primero else '?'}", t,
        f"{ref_api} — `obtener_medicion`", "Incluye timestamp_utc y timestamp_local (UTC-5).")
r, t = get("/mediciones/999999999")
seccion(9, "Consulta por ID inexistente", "GET /mediciones/999999999", t,
        f"{ref_api} — `obtener_medicion`", "Devuelve 404.")
r, t = get(f"/sensores/{sid}/mediciones", limit=5)
seccion(10, "Consulta histórica", f"GET /sensores/{sid}/mediciones?limit=5", t,
        f"{ref_api} — `listar_mediciones` / `get_mediciones`")
ultima = c.get(f"/sensores/{sid}/ultima-medicion").json()
ts = datetime.fromisoformat(ultima["timestamp_utc"].replace("Z", "+00:00")) if "timestamp_utc" in ultima else datetime.now(timezone.utc)
desde, hasta = (ts - timedelta(minutes=5)).isoformat(), ts.isoformat()
r, t = get(f"/sensores/{sid}/mediciones", desde=desde, hasta=hasta)
seccion(11, "Consulta por rango de fechas", f"GET /sensores/{sid}/mediciones?desde={desde}&hasta={hasta}", t,
        f"{ref_api} — `listar_mediciones`", "Solo mediciones dentro del rango (inclusivo).")
r, t = get(f"/sensores/{sid}/mediciones", desde=hasta, hasta=desde)
seccion(12, "Rango desde > hasta", f"GET /sensores/{sid}/mediciones?desde={hasta}&hasta={desde}", t,
        f"{ref_api} — `listar_mediciones`", "Devuelve 400.")
r, t = get(f"/sensores/{sid}/mediciones", limit="abc")
seccion(13, "Validación HTTP incorrecta", f"GET /sensores/{sid}/mediciones?limit=abc", t,
        "FastAPI/Pydantic — parámetro `limit` en `listar_mediciones`", "Devuelve 422.")
r, t = get(f"/sensores/{sid}/ultima-medicion")
seccion(14, "Última medición", f"GET /sensores/{sid}/ultima-medicion", t,
        f"{ref_api} — `obtener_ultima_medicion` / `get_ultima_medicion`")
r, t = get(f"/sensores/{sid}/mediciones", limit=3)
seccion(15, "Últimas N mediciones", f"GET /sensores/{sid}/mediciones?limit=3", t,
        f"{ref_api} — `get_mediciones` (ORDER BY timestamp_utc DESC + LIMIT)")
mags = c.get(f"/sensores/{sid}/magnitudes").json()
mag = mags[0]["magnitud"] if mags else "wind_speed"
r, t = get(f"/sensores/{sid}/mediciones", magnitud=mag, limit=5)
seccion(16, "Filtro por magnitud", f"GET /sensores/{sid}/mediciones?magnitud={mag}&limit=5", t,
        f"{ref_api} — `_ids_magnitudes_del_sensor`")

# ---- FK (17) --------------------------------------------------------------
filas = db.execute(
    select(Medicion.id, Medicion.sensor_magnitud_id).order_by(Medicion.id.desc()).limit(3)).all()
seccion(17, "Claves foráneas", "mediciones.sensor_magnitud_id -> sensor_magnitudes.id -> sensores.id",
        f"Últimas filas (id, sensor_magnitud_id): {filas}\nMagnitudes del sensor: "
        f"{[(m['id'], m['magnitud'], m['unidad']) for m in mags]}",
        "`app/models/*.py` — `ForeignKey(..., ondelete='RESTRICT')`",
        "Cada medición apunta a una configuración sensor↔magnitud, y esta a un sensor.")
seccion(18, "Separación de responsabilidades", "estructura de app/",
        "schemas/ (Pydantic) · models/ (ORM) · crud/ (consultas) · api/ (rutas) · mqtt/ (consumidor) · database/ (conexión)",
        "Ver README, sección 5")

SALIDA.parent.mkdir(exist_ok=True)
SALIDA.write_text("\n".join(out), encoding="utf-8")
print(f"Evidencias escritas en {SALIDA}")