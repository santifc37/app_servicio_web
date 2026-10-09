# Evidencias de pruebas — sensor ENV-003

Generado: 2026-10-09T17:34:22.967587+00:00

## 1. Recepción MQTT

- **Entrada:** `Mensajes del tópico asignado al sensor ENV-003`
- **Resultado:**

```
Registros encontrados para ENV-003:
2026-10-09 12:33:18,466 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:18Z", "measurements": {"wind_speed": {"value": 16.35, "unit": "m/s"}, "wind_direction": {"value": 236.75, "unit": "deg"}}}
2026-10-09 12:33:23,446 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:23Z", "measurements": {"wind_speed": {"value": 3.53, "unit": "m/s"}, "wind_direction": {"value": 83.0, "unit": "deg"}}}
2026-10-09 12:33:28,445 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:28Z", "measurements": {"wind_speed": {"value": 6.98, "unit": "m/s"}, "wind_direction": {"value": 342.87, "unit": "deg"}}}
2026-10-09 12:33:33,455 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:33Z", "measurements": {"wind_speed": {"value": 7.9, "unit": "m/s"}, "wind_direction": {"value": 215.59, "unit": "deg"}}}
2026-10-09 12:33:38,450 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:38Z", "measurements": {"wind_speed": {"value": 6.25, "unit": "m/s"}, "wind_direction": {"value": 192.69, "unit": "deg"}}}
2026-10-09 12:33:43,460 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:43Z", "measurements": {"wind_speed": {"value": 14.83, "unit": "m/s"}, "wind_direction": {"value": 157.15, "unit": "deg"}}}
2026-10-09 12:33:48,491 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:48Z", "measurements": {"wind_speed": {"value": 10.62, "unit": "m/s"}, "wind_direction": {"value": 263.87, "unit": "deg"}}}
2026-10-09 12:33:53,463 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:53Z", "measurements": {"wind_speed": {"value": 0.62, "unit": "m/s"}, "wind_direction": {"value": 191.24, "unit": "deg"}}}
2026-10-09 12:33:58,448 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:33:58Z", "measurements": {"wind_speed": {"value": 16.54, "unit": "m/s"}, "wind_direction": {"value": 151.08, "unit": "deg"}}}
2026-10-09 12:34:03,444 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T17:34:03Z", "measurements": {"wind_speed": {"value": 13.58, "unit": "m/s"}, "wind_direction": {"value": 186.53, "unit": "deg"}}}
```
- **Implementación:** `app/mqtt/client.py` — `ConsumidorMqtt._on_message`
- **Explicación:** Se consulta el registro de ejecución existente. La ausencia de registros no se considera una prueba superada.

## 2. Medición válida almacenada en PostgreSQL

- **Entrada:** `Consultar las últimas 5 mediciones de ENV-003`
- **Resultado:**

```
VERIFICADO: existen mediciones almacenadas para ENV-003.
Registros consultados: 5 (máximo 5).

id | sensor | magnitud | unidad | valor | timestamp_utc
(20596, 'ENV-003', 'wind_direction', 'deg', Decimal('186.5300'), datetime.datetime(2026, 10, 9, 17, 34, 3, tzinfo=datetime.timezone.utc))
(20595, 'ENV-003', 'wind_speed', 'm/s', Decimal('13.5800'), datetime.datetime(2026, 10, 9, 17, 34, 3, tzinfo=datetime.timezone.utc))
(20591, 'ENV-003', 'wind_direction', 'deg', Decimal('151.0800'), datetime.datetime(2026, 10, 9, 17, 33, 58, tzinfo=datetime.timezone.utc))
(20590, 'ENV-003', 'wind_speed', 'm/s', Decimal('16.5400'), datetime.datetime(2026, 10, 9, 17, 33, 58, tzinfo=datetime.timezone.utc))
(20586, 'ENV-003', 'wind_direction', 'deg', Decimal('191.2400'), datetime.datetime(2026, 10, 9, 17, 33, 53, tzinfo=datetime.timezone.utc))
```
- **Implementación:** `app/crud/medicion.py` — `insertar_mediciones`; `app/models/medicion.py` — modelo `Medicion`
- **Explicación:** Se consultan registros reales de PostgreSQL mediante las claves foráneas. No se insertan datos artificiales.

## 3. Sensor inexistente

- **Entrada:** `{"sensor_id": "NOPE-999", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Sensor inexistente: 'NOPE-999'
mediciones antes=20591, después=20591
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 4. Unidad incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "km/h"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Unidad incorrecta en 'wind_speed': recibida 'km/h', esperada 'm/s'
mediciones antes=20591, después=20591
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 5. Tipo de dato incorrecto

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": "caliente", "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Estructura/tipos/timestamp inválidos: measurements.wind_speed.value.float: Input should be a valid number; measurements.wind_speed.value.int: Input should be a valid integer
mediciones antes=20591, después=20591
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 6. Magnitud incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"magnitud_falsa": {"value": 1, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Magnitud 'magnitud_falsa' no pertenece al sensor 'ENV-003'
mediciones antes=20591, después=20591
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 7. Timestamp inválido

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "no-es-fecha", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Estructura/tipos/timestamp inválidos: timestamp: Input should be a valid datetime or date, invalid character in year
mediciones antes=20591, después=20591
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

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
- **Explicación:** La respuesta de una medición incluye timestamp UTC y hora local.

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
- **Explicación:** Se espera HTTP 404.

## 10. Consulta histórica

- **Entrada:** `GET /sensores/39/mediciones?limit=5`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 20596,
    "sensor_magnitud_id": 101,
    "valor": "186.5300",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20595,
    "sensor_magnitud_id": 102,
    "valor": "13.5800",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20591,
    "sensor_magnitud_id": 101,
    "valor": "151.0800",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  },
  {
    "id": 20590,
    "sensor_magnitud_id": 102,
    "valor": "16.5400",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  },
  {
    "id": 20586,
    "sensor_magnitud_id": 101,
    "valor": "191.2400",
    "timestamp_utc": "2026-10-09T17:33:53Z",
    "timestamp_local": "2026-10-09 12:33:53"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones` / `get_mediciones`

## 11. Consulta por rango de fechas

- **Entrada:** `GET /sensores/39/mediciones?desde=2026-10-09T17:29:03+00:00&hasta=2026-10-09T17:34:03+00:00`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 20596,
    "sensor_magnitud_id": 101,
    "valor": "186.5300",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20595,
    "sensor_magnitud_id": 102,
    "valor": "13.5800",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20591,
    "sensor_magnitud_id": 101,
    "valor": "151.0800",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  },
  {
    "id": 20590,
    "sensor_magnitud_id": 102,
    "valor": "16.5400",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  },
  {
    "id": 20586,
    "sensor_magnitud_id": 101,
    "valor": "191.2400",
    "timestamp_utc": "2026-10-09T17:33:53Z",
    "timestamp_local": "2026-10-09 12:33:53"
  },
  {
    "id": 20585,
    "sensor_magnitu
... (recortado)
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones`
- **Explicación:** Consulta el histórico con límites temporales.

## 12. Rango desde > hasta

- **Entrada:** `GET /sensores/39/mediciones?desde=2026-10-09T17:34:03+00:00&hasta=2026-10-09T17:29:03+00:00`
- **Resultado:**

```
HTTP 400
{
  "detail": "El parámetro desde no puede ser mayor que hasta"
}
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `listar_mediciones`
- **Explicación:** Se espera HTTP 400.

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
- **Implementación:** FastAPI/Pydantic — parámetro `limit`
- **Explicación:** Se espera HTTP 422.

## 14. Última medición

- **Entrada:** `GET /sensores/39/ultima-medicion`
- **Resultado:**

```
HTTP 200
{
  "id": 20596,
  "sensor_magnitud_id": 101,
  "valor": "186.5300",
  "timestamp_utc": "2026-10-09T17:34:03Z",
  "timestamp_local": "2026-10-09 12:34:03"
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
    "id": 20596,
    "sensor_magnitud_id": 101,
    "valor": "186.5300",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20595,
    "sensor_magnitud_id": 102,
    "valor": "13.5800",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20591,
    "sensor_magnitud_id": 101,
    "valor": "151.0800",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `get_mediciones`
- **Explicación:** Comprueba la consulta limitada a tres registros.

## 16. Filtro por magnitud

- **Entrada:** `GET /sensores/39/mediciones?magnitud=wind_direction&limit=5`
- **Resultado:**

```
HTTP 200
[
  {
    "id": 20596,
    "sensor_magnitud_id": 101,
    "valor": "186.5300",
    "timestamp_utc": "2026-10-09T17:34:03Z",
    "timestamp_local": "2026-10-09 12:34:03"
  },
  {
    "id": 20591,
    "sensor_magnitud_id": 101,
    "valor": "151.0800",
    "timestamp_utc": "2026-10-09T17:33:58Z",
    "timestamp_local": "2026-10-09 12:33:58"
  },
  {
    "id": 20586,
    "sensor_magnitud_id": 101,
    "valor": "191.2400",
    "timestamp_utc": "2026-10-09T17:33:53Z",
    "timestamp_local": "2026-10-09 12:33:53"
  },
  {
    "id": 20581,
    "sensor_magnitud_id": 101,
    "valor": "263.8700",
    "timestamp_utc": "2026-10-09T17:33:48Z",
    "timestamp_local": "2026-10-09 12:33:48"
  },
  {
    "id": 20576,
    "sensor_magnitud_id": 101,
    "valor": "157.1500",
    "timestamp_utc": "2026-10-09T17:33:43Z",
    "timestamp_local": "2026-10-09 12:33:43"
  }
]
```
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `_ids_magnitudes_del_sensor`

## 17. Claves foráneas

- **Entrada:** `mediciones.sensor_magnitud_id -> sensor_magnitudes.id -> sensores.id`
- **Resultado:**

```
Últimas filas relacionadas (medicion_id, sensor_magnitud_id, sensor_id, codigo):
(20596, 101, 39, 'ENV-003')
(20595, 102, 39, 'ENV-003')
(20591, 101, 39, 'ENV-003')
```
- **Implementación:** `app/models/medicion.py`, `sensor_magnitud.py`, `sensor.py`
- **Explicación:** Se consultan las relaciones reales mediante JOIN y las claves foráneas definidas en los modelos.

## 18. Separación de responsabilidades

- **Entrada:** `Estructura de app/`
- **Resultado:**

```
schemas/ (Pydantic) · models/ (ORM) · crud/ (consultas) · api/ (rutas) · mqtt/ (consumidor) · database/ (conexión)
```
- **Implementación:** README.md, sección 5; estructura de directorios del proyecto
- **Explicación:** Descripción de la organización modular del código.

