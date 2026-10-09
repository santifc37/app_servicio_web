# Informe Taller 2 — API IoT con FastAPI, MQTT y PostgreSQL

> Informe del taller (sección 8 de la guía). Los datos del sensor `ENV-003` han sido recolectados y validados exitosamente contra PostgreSQL.

## 1. Información General

| Campo | Valor |
|---|---|
| Nombre del proyecto | API IoT — adquisición, validación y consulta de mediciones |
| Integrantes | Eddy Santiago Giraldo Ceballos |
| Asignatura | Aplicaciones y Servicios Web |
| Fecha | 09 de octubre de 2026 |
| Sensor asignado | `ENV-003` |
| Tópico MQTT utilizado | `iot/sensors/ENV-003/data` |

## 2. Descripción del Sistema

- **Problema resuelto:** Una infraestructura IoT publica mediciones del sensor de ambiente `ENV-003` mediante el protocolo MQTT. La aplicación se suscribe al tópico asignado, valida los mensajes recibidos con Pydantic, verifica la existencia y rangos del sensor mediante SQLAlchemy ORM en PostgreSQL, y almacena únicamente las mediciones válidas. Finalmente, expone la información a través de endpoints REST con soporte para zonas horarias (conversión a hora local de Colombia).
- **Arquitectura implementada:** FastAPI (endpoints REST) + consumidor MQTT (`paho-mqtt` ejecutado en un hilo secundario) + validación Pydantic + SQLAlchemy ORM contra PostgreSQL. El consumidor y la API comparten un único proceso sin interferir en la recepción asíncrona de mensajes.
- **Magnitudes y unidades recibidas:**
  - `wind_direction` (Dirección del viento): en grados (`deg`).
  - `wind_speed` (Velocidad del viento): en metros por segundo (`m/s`).
- **Payload real del sensor:**

  ```json
  {
    "sensor_id": "ENV-003",
    "timestamp": "2026-10-09T14:57:48Z",
    "measurements": {
      "wind_direction": {
        "value": 152.16,
        "unit": "deg"
      },
      "wind_speed": {
        "value": 0.18,
        "unit": "m/s"
      }
    }
  }
  ```

## 3. Configuración del Entorno

1. Crear el entorno virtual: `python -m venv .venv`
2. Activar el entorno virtual:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Variables de entorno (archivo `.env`, dentro de `.gitignore`; ver `.env.example`):
   - `MQTT_BROKER`, `MQTT_PORT`, `MQTT_TOPIC`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_KEEPALIVE`
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
5. Ejecutar la API: `python -m uvicorn app.main:app` (El proceso arranca automáticamente el consumidor MQTT).
6. Pruebas automáticas: `python -m pytest -q`
7. Generar evidencias contra la BD real: `python scripts/generar_evidencias.py`

## 4. Base de Datos

- **Conexión:** PostgreSQL remoto (`appdb`, esquema `public`) mediante SQLAlchemy y el driver `psycopg2`.
- **Tablas utilizadas:**
  - `sensores` — catálogo de sensores (id, código, nombre, ubicación, estado).
  - `sensor_magnitudes` — relación entre sensores, magnitudes permitidas y unidades.
  - `mediciones` — registro de lecturas válidas almacenadas (id, sensor_magnitud_id, valor, timestamp_utc).
- **Relaciones implementadas:**
  - `sensores` 1:N `sensor_magnitudes` (`ON DELETE RESTRICT`).
  - `sensor_magnitudes` 1:N `mediciones` (`ON DELETE RESTRICT`).

## 5. Organización del Código

| Directorio | Función |
|---|---|
| `app/schemas/` | Modelos Pydantic para validación de mensajes MQTT y serialización de respuestas HTTP. |
| `app/models/` | Clases ORM de SQLAlchemy que mapean las tablas de PostgreSQL. |
| `app/crud/` | Lógica de acceso a datos (consultas SELECT e inserciones en PostgreSQL). |
| `app/api/` | Routers de FastAPI con endpoints REST y manejo de excepciones HTTP. |
| `app/mqtt/` | Cliente MQTT, suscripción, decodificación y pipeline de validación. |
| `app/database/` | Configuración del motor SQLAlchemy, sesión de base de datos y dependencias. |
| `app/main.py` | Punto de entrada de la aplicación, inicio del hilo MQTT y registro de rutas. |

## 6. Endpoints Implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/sensores` | Lista todos los sensores registrados. |
| GET | `/sensores/{id}` | Obtiene la información de un sensor por ID (`404` si no existe). |
| GET | `/sensores/por-codigo/{codigo}` | Obtiene la información de un sensor por su código, ej. `ENV-003`. |
| GET | `/sensores/{id}/magnitudes` | Muestra las magnitudes configuradas para el sensor. |
| GET | `/sensor-magnitudes/{id}` | Detalle de la configuración sensor-magnitud por ID. |
| GET | `/mediciones/{id}` | Obtiene una medición individual por su ID (`404` si no existe). |
| GET | `/sensores/{id}/mediciones` | Histórico con filtros `magnitud`, `desde`, `hasta`, `limit` (`400` si `desde > hasta`). |
| GET | `/sensores/{id}/ultima-medicion` | Devuelve la medición más reciente del sensor. |

*Todas las respuestas con mediciones convierten el `timestamp_utc` almacenado a `timestamp_local` (Hora de Colombia UTC-5).*

## 7. Evidencias de Funcionamiento

| # | Prueba | Estado | Implementación / Archivo |
|---|---|---|---|
| 1 | Recepción MQTT desde el tópico asignado | ✅ | `app/mqtt/client.py` (`on_message`) |
| 2 | Medición válida almacenada en PostgreSQL | ✅ | `app/crud/medicion.py` (`insertar_mediciones`) |
| 3 | Sensor inexistente → mensaje rechazado | ✅ | `app/mqtt/client.py` (`validar_payload`) |
| 4 | Unidad incorrecta → mensaje rechazado | ✅ | `app/mqtt/client.py` (`validar_payload`) |
| 5 | Tipo de dato incorrecto → mensaje rechazado | ✅ | `app/mqtt/client.py` (`validar_payload`) |
| 6 | Magnitud incorrecta → mensaje rechazado | ✅ | `app/mqtt/client.py` (`validar_payload`) |
| 7 | Timestamp inválido → mensaje rechazado | ✅ | `app/mqtt/client.py` (`validar_payload`) |
| 8 | Consulta por ID existente → respuesta correcta | ✅ | `app/api/medicion.py` (`obtener_medicion`) |
| 9 | Consulta por ID inexistente → `404` | ✅ | `app/api/medicion.py` (`obtener_medicion`) |
| 10 | Consulta histórica → datos retornados | ✅ | `app/api/medicion.py` (`listar_mediciones`) |
| 11 | Consulta por rango de fechas → datos filtrados | ✅ | `app/crud/medicion.py` (`get_mediciones`) |
| 12 | Rango `desde > hasta` → `400` | ✅ | `app/api/medicion.py` (`listar_mediciones`) |
| 13 | Validación HTTP incorrecta → `422` | ✅ | Validadores FastAPI / Pydantic |
| 14 | Última medición → registro más reciente | ✅ | `app/crud/medicion.py` (`get_ultima_medicion`) |
| 15 | Últimas N mediciones → uso correcto de `limit` | ✅ | `app/crud/medicion.py` (`get_mediciones`) |
| 16 | Filtro por magnitud → resultado filtrado | ✅ | `app/crud/medicion.py` (`get_mediciones`) |
| 17 | Claves foráneas → relación implementada correctamente | ✅ | `app/models/medicion.py` (`ForeignKey`) |
| 18 | Separación de responsabilidades → organización | ✅ | Estructura modular en `app/` |

## 8. Control de versiones

El proyecto se desarrolló de manera individual por **Eddy Santiago Giraldo Ceballos** y se utilizó Git y GitHub para almacenar y gestionar el código fuente.

Durante el desarrollo no se realizaron commits intermedios de forma sistemática. Por esta razón, el historial de versiones no refleja individualmente cada etapa de implementación, corrección y documentación del proyecto.

El repositorio permite consultar los archivos del proyecto y su documentación en la rama `taller-2`.

Las principales actividades realizadas fueron:

* Desarrollo de la API REST utilizando FastAPI.
* Configuración e integración de PostgreSQL para el almacenamiento de las mediciones.
* Implementación del consumidor MQTT para la recepción y validación de datos de los sensores.
* Implementación y verificación de los endpoints de la API.
* Elaboración del informe de evidencias y documentación del proyecto.
* Ejecución de las pruebas automatizadas, con un resultado de **20 pruebas aprobadas**.


## 9. Conclusiones

- **Principales aprendizajes:** Se logró integrar con éxito un protocolo asíncrono y liviano como MQTT con una API REST síncrona en FastAPI, garantizando integridad de datos mediante Pydantic y ORM.
- **Dificultades encontradas:** La gestión de zonas horarias al recibir marcas de tiempo en formato ISO UTC y proyectarlas correctamente en hora local colombiana (UTC-5) para el usuario final.
- **Soluciones aplicadas:** Se estandarizó el almacenamiento persistente exclusivamente en UTC dentro de PostgreSQL y se realizó la conversión a hora local dentro de la capa de serialización (Schemas Pydantic) de los GET HTTP.
