# Evidencias de pruebas — sensor ENV-003

Generado: 2026-10-09T16:36:12.348658+00:00

## 3. Sensor inexistente

- **Entrada:** `{"sensor_id": "NOPE-999", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO: Sensor inexistente: 'NOPE-999'
mediciones antes=18088 después=18088 -> no almacenado OK
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** El mensaje se rechaza y se registra; no se inserta ninguna fila.

## 4. Unidad incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "km/h"}}}`
- **Resultado:**

```
RECHAZADO: Unidad incorrecta en 'wind_speed': recibida 'km/h', esperada 'm/s'
mediciones antes=18088 después=18088 -> no almacenado OK
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** El mensaje se rechaza y se registra; no se inserta ninguna fila.

## 5. Tipo de dato incorrecto

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": "caliente", "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO: Estructura/tipos/timestamp inválidos: measurements.wind_speed.value.float: Input should be a valid number; measurements.wind_speed.value.int: Input should be a valid integer
mediciones antes=18088 después=18088 -> no almacenado OK
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** El mensaje se rechaza y se registra; no se inserta ninguna fila.

## 6. Magnitud incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"magnitud_falsa": {"value": 1, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO: Magnitud 'magnitud_falsa' no pertenece al sensor 'ENV-003'
mediciones antes=18088 después=18088 -> no almacenado OK
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** El mensaje se rechaza y se registra; no se inserta ninguna fila.

## 7. Timestamp inválido

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "no-es-fecha", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO: Estructura/tipos/timestamp inválidos: timestamp: Input should be a valid datetime or date, invalid character in year
mediciones antes=18088 después=18088 -> no almacenado OK
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** El mensaje se rechaza y se registra; no se inserta ninguna fila.

## 8. Consulta por ID existente

- **Entrada:** `GET /mediciones/10`
- **Resultado:**

```
HTTP 200
{
  "id": 10,
  "sensor_magnitud_id": 6,
  "valor": "35.1000",
  "timestamp_utc": "2026-10-08T06:35:13Z",
  "timestamp_local": "2026-10-08 01:35:13"
}
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `obtener_medicion`
- **Explicación:** Incluye timestamp_utc y timestamp_local (UTC-5).

## 9. Consulta por ID inexistente

- **Entrada:** `GET /mediciones/999999999`
- **Resultado:**

```
HTTP 404
{
  "detail": "Medición no encontrada"
}
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `obtener_medicion`
- **Explicación:** Devuelve 404.

## 10. Consulta histórica

- **Entrada:** `GET /sensores/39/mediciones?limit=5`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 15026,
    "sensor_magnitud_id": 102,
    "valor": "1.9500",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15027,
    "sensor_magnitud_id": 101,
    "valor": "277.5800",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15021,
    "sensor_magnitud_id": 102,
    "valor": "9.1800",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  },
  {
    "id": 15022,
    "sensor_magnitud_id": 101,
    "valor": "125.2200",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  },
  {
    "id": 14743,
    "sensor_magnitud_id": 102,
    "valor": "0.1800",
    "timestamp_utc": "2026-10-09T14:57:48Z",
    "timestamp_local": "2026-10-09 09:57:48"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones` / `get_mediciones`

## 11. Consulta por rango de fechas

- **Entrada:** `GET /sensores/39/mediciones?desde=2026-10-09T15:00:53+00:00&hasta=2026-10-09T15:05:53+00:00`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 15026,
    "sensor_magnitud_id": 102,
    "valor": "1.9500",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15027,
    "sensor_magnitud_id": 101,
    "valor": "277.5800",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15021,
    "sensor_magnitud_id": 102,
    "valor": "9.1800",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  },
  {
    "id": 15022,
    "sensor_magnitud_id": 101,
    "valor": "125.2200",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones`
- **Explicación:** Solo mediciones dentro del rango (inclusivo).

## 12. Rango desde > hasta

- **Entrada:** `GET /sensores/39/mediciones?desde=2026-10-09T15:05:53+00:00&hasta=2026-10-09T15:00:53+00:00`
- **Resultado:**

```
HTTP 400
{
  "detail": "El parámetro desde no puede ser mayor que hasta"
}
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones`
- **Explicación:** Devuelve 400.

## 13. Validación HTTP incorrecta

- **Entrada:** `GET /sensores/39/mediciones?limit=abc`
- **Resultado:**

```
HTTP 422
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "query",
        "limit"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
    }
  ]
}
```
- **Implementación:** FastAPI/Pydantic — parámetro `limit` en `listar_mediciones`
- **Explicación:** Devuelve 422.

## 14. Última medición

- **Entrada:** `GET /sensores/39/ultima-medicion`
- **Resultado:**

```
HTTP 200
{
  "id": 15026,
  "sensor_magnitud_id": 102,
  "valor": "1.9500",
  "timestamp_utc": "2026-10-09T15:05:53Z",
  "timestamp_local": "2026-10-09 10:05:53"
}
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `obtener_ultima_medicion` / `get_ultima_medicion`

## 15. Últimas N mediciones

- **Entrada:** `GET /sensores/39/mediciones?limit=3`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 15026,
    "sensor_magnitud_id": 102,
    "valor": "1.9500",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15027,
    "sensor_magnitud_id": 101,
    "valor": "277.5800",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15021,
    "sensor_magnitud_id": 102,
    "valor": "9.1800",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `get_mediciones` (ORDER BY timestamp_utc DESC + LIMIT)

## 16. Filtro por magnitud

- **Entrada:** `GET /sensores/39/mediciones?magnitud=wind_direction&limit=5`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 15027,
    "sensor_magnitud_id": 101,
    "valor": "277.5800",
    "timestamp_utc": "2026-10-09T15:05:53Z",
    "timestamp_local": "2026-10-09 10:05:53"
  },
  {
    "id": 15022,
    "sensor_magnitud_id": 101,
    "valor": "125.2200",
    "timestamp_utc": "2026-10-09T15:05:48Z",
    "timestamp_local": "2026-10-09 10:05:48"
  },
  {
    "id": 14744,
    "sensor_magnitud_id": 101,
    "valor": "152.1600",
    "timestamp_utc": "2026-10-09T14:57:48Z",
    "timestamp_local": "2026-10-09 09:57:48"
  },
  {
    "id": 14739,
    "sensor_magnitud_id": 101,
    "valor": "116.7400",
    "timestamp_utc": "2026-10-09T14:57:43Z",
    "timestamp_local": "2026-10-09 09:57:43"
  },
  {
    "id": 14734,
    "sensor_magnitud_id": 101,
    "valor": "94.3200",
    "timestamp_utc": "2026-10-09T14:57:38Z",
    "timestamp_local": "2026-10-09 09:57:38"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `_ids_magnitudes_del_sensor`

## 17. Claves foráneas

- **Entrada:** `mediciones.sensor_magnitud_id -> sensor_magnitudes.id -> sensores.id`
- **Resultado:**

```
Últimas filas (id, sensor_magnitud_id): [(18105, 1), (18104, 2), (18103, 3)]
Magnitudes del sensor: [(101, 'wind_direction', 'deg'), (102, 'wind_speed', 'm/s')]
```
- **Implementación:** `app/models/*.py` — `ForeignKey(..., ondelete='RESTRICT')`
- **Explicación:** Cada medición apunta a una configuración sensor↔magnitud, y esta a un sensor.

## 18. Separación de responsabilidades

- **Entrada:** `estructura de app/`
- **Resultado:**

```
schemas/ (Pydantic) · models/ (ORM) · crud/ (consultas) · api/ (rutas) · mqtt/ (consumidor) · database/ (conexión)
```
- **Implementación:** Ver README, sección 5
