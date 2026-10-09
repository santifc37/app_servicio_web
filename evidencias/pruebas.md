# Evidencias de pruebas — sensor ENV-003

Generado: 2026-10-09T17:06:01.861438+00:00

## 1. Recepción MQTT

- **Entrada:** `Mensajes del tópico asignado al sensor ENV-003`
- **Resultado:**

```
Registros encontrados para ENV-003:
2026-10-09 09:57:17,749 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:18Z", "measurements": {"wind_speed": {"value": 16.78, "unit": "m/s"}, "wind_direction": {"value": 281.37, "unit": "deg"}}}
2026-10-09 09:57:22,748 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:23Z", "measurements": {"wind_speed": {"value": 19.6, "unit": "m/s"}, "wind_direction": {"value": 176.69, "unit": "deg"}}}
2026-10-09 09:57:27,751 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:28Z", "measurements": {"wind_speed": {"value": 15.89, "unit": "m/s"}, "wind_direction": {"value": 132.84, "unit": "deg"}}}
2026-10-09 09:57:32,761 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:33Z", "measurements": {"wind_speed": {"value": 19.72, "unit": "m/s"}, "wind_direction": {"value": 296.33, "unit": "deg"}}}
2026-10-09 09:57:37,784 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:38Z", "measurements": {"wind_speed": {"value": 7.74, "unit": "m/s"}, "wind_direction": {"value": 94.32, "unit": "deg"}}}
2026-10-09 09:57:42,760 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:43Z", "measurements": {"wind_speed": {"value": 6.5, "unit": "m/s"}, "wind_direction": {"value": 116.74, "unit": "deg"}}}
2026-10-09 09:57:47,791 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:57:48Z", "measurements": {"wind_speed": {"value": 0.18, "unit": "m/s"}, "wind_direction": {"value": 152.16, "unit": "deg"}}}
2026-10-09 10:05:47,670 [INFO] Conectado a emqx.coriotlab.co:1883 y suscrito a iot/sensors/ENV-003/data
2026-10-09 10:05:47,775 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T15:05:48Z", "measurements": {"wind_speed": {"value": 9.18, "unit": "m/s"}, "wind_direction": {"value": 125.22, "unit": "deg"}}}
2026-10-09 10:05:52,813 [INFO] RECIBIDO iot/sensors/ENV-003/data: {"sensor_id": "ENV-003", "timestamp": "2026-10-09T15:05:53Z", "measurements": {"wind_speed": {"value": 1.95, "unit": "m/s"}, "wind_direction": {"value": 277.58, "unit": "deg"}}}
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
(15026, 'ENV-003', 'wind_speed', 'm/s', Decimal('1.9500'), datetime.datetime(2026, 10, 9, 15, 5, 53, tzinfo=datetime.timezone.utc))
(15027, 'ENV-003', 'wind_direction', 'deg', Decimal('277.5800'), datetime.datetime(2026, 10, 9, 15, 5, 53, tzinfo=datetime.timezone.utc))
(15021, 'ENV-003', 'wind_speed', 'm/s', Decimal('9.1800'), datetime.datetime(2026, 10, 9, 15, 5, 48, tzinfo=datetime.timezone.utc))
(15022, 'ENV-003', 'wind_direction', 'deg', Decimal('125.2200'), datetime.datetime(2026, 10, 9, 15, 5, 48, tzinfo=datetime.timezone.utc))
(14743, 'ENV-003', 'wind_speed', 'm/s', Decimal('0.1800'), datetime.datetime(2026, 10, 9, 14, 57, 48, tzinfo=datetime.timezone.utc))

Registros de almacenamiento MQTT:
No se encontraron líneas ALMACENADO que mencionen explícitamente ENV-003.
```
- **Implementación:** `app/crud/medicion.py` — `insertar_mediciones`; `app/models/medicion.py` — modelo `Medicion`
- **Explicación:** Se consultan registros reales de PostgreSQL mediante las claves foráneas y se añade evidencia del registro MQTT.

## 3. Sensor inexistente

- **Entrada:** `{"sensor_id": "NOPE-999", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Sensor inexistente: 'NOPE-999'
mediciones antes=19114, después=19114
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 4. Unidad incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": 12.5, "unit": "km/h"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Unidad incorrecta en 'wind_speed': recibida 'km/h', esperada 'm/s'
mediciones antes=19114, después=19114
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 5. Tipo de dato incorrecto

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"wind_speed": {"value": "caliente", "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Estructura/tipos/timestamp inválidos: measurements.wind_speed.value.float: Input should be a valid number; measurements.wind_speed.value.int: Input should be a valid integer
mediciones antes=19114, después=19114
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 6. Magnitud incorrecta

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "2026-10-09T14:00:00Z", "measurements": {"magnitud_falsa": {"value": 1, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Magnitud 'magnitud_falsa' no pertenece al sensor 'ENV-003'
mediciones antes=19114, después=19114
No hubo cambios en el total de mediciones.
```
- **Implementación:** `app/mqtt/client.py` — `validar_payload` / `construir_mediciones`
- **Explicación:** Se comprueba el rechazo y se compara el total de filas antes y después.

## 7. Timestamp inválido

- **Entrada:** `{"sensor_id": "ENV-003", "timestamp": "no-es-fecha", "measurements": {"wind_speed": {"value": 12.5, "unit": "m/s"}}}`
- **Resultado:**

```
RECHAZADO correctamente: Estructura/tipos/timestamp inválidos: timestamp: Input should be a valid datetime or date, invalid character in year
mediciones antes=19114, después=19114
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
- **Explicación:** Consulta el histórico con límites temporales.

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
- **Implementación:** `app/api/medicion.py` / `app/crud/medicion.py` — `get_mediciones`
- **Explicación:** Comprueba la consulta limitada a tres registros.

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
Últimas filas relacionadas (medicion_id, sensor_magnitud_id, sensor_id, codigo):
(15027, 101, 39, 'ENV-003')
(15026, 102, 39, 'ENV-003')
(15022, 101, 39, 'ENV-003')
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

