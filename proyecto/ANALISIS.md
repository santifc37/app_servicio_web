# Análisis de Integración y Normalización de Datos

## 0. Mapeo y Correspondencia de Contratos

A continuación se detallan las correspondencias entre los campos de cada proveedor y el contrato institucional de la universidad:

| Campo Contrato Institucional | Tipo Requerido | Campo Proveedor A (JSON) | Campo Proveedor B (CSV) | Transformaciones y Reglas Aplicadas |
| :--- | :--- | :--- | :--- | :--- |
| `ciudad` | String (no vacío) | `station.city_name` | `municipality` | Extraer texto. Descartar registro si viene nulo o vacío (`""`). |
| `pais` | String (no vacío) | `station.country_code` | `country` | Extraer código/nombre del país. Debe ser texto no vacío. |
| `latitud` | Number (-90 a 90) | `location.lat` | `latitude_deg` | Convertir a flotante (`float`). Debe estar en el rango [-90, 90]. |
| `longitud` | Number (-180 a 180) | `location.lon` | `longitude_deg` | Convertir a flotante (`float`). Debe estar en el rango [-180, 180]. |
| `temperatura_c` | Number | `measurements.temperature_f` | `temp_celsius` | **A:** Convertir de °F a °C: `(F - 32) * 5/9`. <br>**B:** Convertir a float directamente. |
| `humedad` | Number (0 a 100) | `measurements.relative_humidity` | `humidity_pct` | Convertir a float. Debe estar en el rango [0, 100]. |
| `viento_kmh` | Number (>= 0) | `measurements.wind_speed_ms` | `wind_kmh` | **A:** Convertir de m/s a km/h: `ms * 3.6`. <br>**B:** Convertir a float directamente. Debe ser >= 0. |
| `fecha_hora` | String (ISO 8601) | `observed_at` | `measurement_time` | **A:** Viene en ISO 8601, validar parseo. <br>**B:** Parsear desde `DD/MM/YYYY HH:MM` a formato ISO 8601. |
| `origen` | String | Valor fijo | Valor fijo | Asignar `"proveedor_a"` o `"proveedor_b"` según la fuente original. |

---

## 1. ¿Qué diferencias encontró entre los contratos de los proveedores?

* **Estructura:** el Proveedor A entrega JSON anidado (`station`, `location`, `measurements`), mientras que el Proveedor B entrega un CSV plano delimitado por `;`.
* **Unidades:** la temperatura de A viene en Fahrenheit y la de B en Celsius; el viento de A viene en m/s y el de B ya en km/h.
* **Formato de fecha:** A usa ISO 8601 con zona horaria (`YYYY-MM-DDTHH:MM:SS-05:00`); B usa texto local `DD/MM/YYYY HH:MM`.
* **Nombres de campo:** ningún campo se llama igual entre proveedores ni coincide con el nombre exigido por el contrato institucional (ej. `city_name` vs `municipality` vs `ciudad`).
* **Calidad de los datos:** ambos proveedores incluyen registros con campos vacíos, nulos, valores no numéricos (`"N/A"`, `"error"`) y valores fuera de rango, pero no de forma idéntica: A usa `null`/`"N/A"` para marcar ausencia, B usa cadenas vacías `""`.

## 2. ¿Qué transformaciones fueron necesarias?

* **Temperatura (°F → °C):** `(F - 32) * 5/9`, aplicada solo a Proveedor A.
* **Viento (m/s → km/h):** `ms * 3.6`, aplicada solo a Proveedor A.
* **Fecha a ISO 8601:** para A se valida el parseo con `datetime.fromisoformat()`; para B se parsea `DD/MM/YYYY HH:MM` con `datetime.strptime()` y se reconvierte a ISO 8601 con `.isoformat()`.
* **Tipado:** todos los campos numéricos de B llegan como texto desde el CSV y deben convertirse explícitamente a `float`.
* **Normalización de nombres de campo:** mapeo de cada campo de origen al nombre exacto exigido por el contrato institucional (tabla de la sección 0).
* **Asignación de `origen`:** valor fijo (`"proveedor_a"` / `"proveedor_b"`) según la fuente, ya que ningún proveedor lo entrega directamente.

## 3. ¿Qué tipos de errores encontró antes de enviar información?

Se identificaron dos categorías, según la sección 3 del README:

**a) Errores de normalización** (el dato no se puede representar en el tipo exigido por el contrato — 12 de 400 registros):
| Ejemplo | Motivo |
|---|---|
| `proveedor_a_40` | `observed_at` ausente |
| `proveedor_a_82` | `temperature_f: "N/A"` |
| `proveedor_a_136` | `city_name` vacío |
| `proveedor_a_174` | fecha corrupta (`"09-XX-2026 25:61"`) |
| `proveedor_b_76` | `measurement_time` vacío |
| `proveedor_b_114` | `temp_celsius: "error"` (no numérico) |
| `proveedor_b_171` | fecha inválida (`"31/13/2026 28:75"`) |

**b) Registros rechazados localmente** (se normalizan correctamente, pero violan una regla de negocio del contrato — 8 de 388 normalizados):
| Ejemplo | Motivo |
|---|---|
| `proveedor_a_15` | humedad 108.4 (fuera de 0–100) |
| `proveedor_a_31` | latitud 95.245 (fuera de -90 a 90) |
| `proveedor_a_88` | viento -8.64 (negativo) |
| `proveedor_b_190` | longitud 188.45 (fuera de -180 a 180) |

**Criterio usado para distinguir ambos:** un campo vacío o de tipo incorrecto (no se puede construir un valor válido) se trata como error de normalización, porque no hay un dato representable que enviar a validación. Un campo presente y del tipo correcto pero fuera del rango permitido por el contrato (latitud, longitud, humedad, viento) sí se normaliza y se rechaza en la validación local, porque el dato existe y es sintácticamente válido, solo incumple una regla de negocio.

## 4. ¿Qué diferencias encontró entre validación local y validación del servidor?

La validación local solo puede verificar reglas que están documentadas explícitamente en el contrato de datos (rangos numéricos, campos no vacíos, valores permitidos de `origen`). No puede verificar reglas que el servidor aplica pero que el contrato no detalla, ni el estado interno del servidor (qué ya fue guardado antes).

Esto se comprobó en la práctica, con dos ejemplos concretos:

* **Formato de fecha:** el contrato exige `fecha_hora` en "formato ISO 8601", pero no especifica si debe incluir zona horaria. La validación local, siguiendo la letra del contrato, aceptaba fechas ISO 8601 sin zona horaria (ej. `"2026-09-01T06:00:00"`, generadas a partir del CSV de Proveedor B, que no trae huso horario). El servidor, sin embargo, rechazó esos envíos con `422` y el mensaje *"fecha_hora debe incluir zona horaria, por ejemplo Z o -05:00"*. Fue necesario ajustar el normalizador para asumir explícitamente la zona horaria de Colombia (`-05:00`) en los datos de Proveedor B.
* **Duplicidad:** al reenviar registros que ya habían sido aceptados en una ejecución previa, el servidor los rechazó con `409` (*"La medición ya existe"*). Esta es una regla de estado que ningún cliente puede validar localmente, porque depende de lo que el servidor ya tiene almacenado.

En resumen:
* **Validación local:** determinista, basada únicamente en el contrato de datos (tipos, rangos, campos obligatorios) tal como está escrito. Se ejecuta sin red y evita envíos innecesarios, pero puede pasar por alto reglas que el contrato no detalla explícitamente.
* **Validación del servidor:** además de repetir las reglas de datos, aplica reglas más estrictas o implícitas (formato exacto de fecha) y reglas de estado (duplicados) que el cliente no controla ni puede anticipar sin haber interactuado antes con la API real. Es la validación que finalmente decide si el registro queda almacenado.

## 5. ¿Qué decisión de implementación considera más importante y por qué?

La decisión más importante fue **mantener un identificador de trazabilidad interno (`_trazabilidad_id`) en cada registro durante todo el pipeline, sin incluirlo en el body enviado a la API**.

Esto permite que, en cualquier punto del proceso (normalización, validación local, envío HTTP), el registro conserve su identidad y se pueda reportar exactamente qué pasó con él — algo indispensable para el reporte final exigido en la sección 10 del README. Al mismo tiempo, como el contrato institucional no define ese campo, se excluye explícitamente del body (`{k: v for k, v in payload.items() if not k.startswith("_")}`) antes de cada `POST`, evitando que el servidor rechace la solicitud por un campo no reconocido.

Sin esta separación entre "dato de trazabilidad interno" y "dato del contrato", habría sido imposible construir un reporte con trazabilidad por registro sin arriesgar que la API rechazara el body por campos extra, o habría obligado a mantener listas paralelas propensas a desincronizarse.

---

## Evidencia de ejecución real

Ejecución sobre los 400 registros de `datos/proveedor_a.json` (200) y `datos/proveedor_b.csv` (200), contra la API institucional (`EQUIPO-02-APPSWEB`):

| Métrica | Valor |
|---|---:|
| Registros procesados | 400 |
| Registros normalizados | 388 |
| Errores de normalización | 12 |
| Válidos localmente | 380 |
| Rechazados localmente | 8 |
| Registros enviados a la API | 380 |
| Aceptados por la API | 380 (acumulado en dos ejecuciones; ver nota) |
| Rechazados por la API | variable según ejecución (ver nota) |
| Errores de comunicación | 0 |

**Caso de error de normalización:** `proveedor_a_40` — el campo `observed_at` viene ausente, por lo que no es posible construir una fecha válida; el registro queda excluido de `salida/normalizadas.json` y marcado como `error_normalizacion` en el reporte.

**Caso de rechazo local:** `proveedor_a_15` — se normaliza correctamente (`humedad: 108.4`), pero al validar contra el contrato (rango 0–100) queda como `rechazado_localmente`; permanece en `salida/normalizadas.json` pero no se envía a la API.

**Caso de aceptación real por la API (`201`):**
```json
"proveedor_b_189": {
  "resultado": "aceptado_api",
  "status_code": 201,
  "respuesta_api": {
    "id": 379,
    "estado": "aceptada",
    "mensaje": "Medición registrada correctamente"
  }
}
```

**Caso de rechazo real por la API (`409`, no `422`):**
```json
"proveedor_a_1": {
  "resultado": "rechazado_api",
  "status_code": 409,
  "respuesta_api": { "detail": "La medición ya existe" }
}
```

**Nota sobre las dos ejecuciones:** en una primera ejecución contra la API real, el registro `fecha_hora` de Proveedor B se enviaba en formato ISO 8601 sin zona horaria (ej. `"2026-09-01T06:00:00"`), y el servidor respondió con `422` indicando que el campo debe incluir zona horaria explícita (`Z` o `-05:00`), algo que el contrato no especifica de forma explícita y que la validación local no podía anticipar. Se corrigió el normalizador para asumir la zona horaria de Colombia (`-05:00`) en los datos de Proveedor B, dado que todas las ciudades del dataset son colombianas. Tras el ajuste, los 190 registros de Proveedor B fueron aceptados (`201`); los 190 de Proveedor A, que ya habían sido aceptados en la ejecución anterior, fueron rechazados en la segunda corrida con `409` por ser duplicados. Ambas ejecuciones en conjunto demuestran que el 100% de los 380 registros válidos localmente terminaron siendo aceptados por el servidor.

**Consulta final (`GET /api/v1/mediciones?equipo=EQUIPO-02-APPSWEB`):** devuelve `"total": 380`, con el detalle de cada medición almacenada (incluyendo `id` asignado por el servidor y `fecha_recepcion`), confirmando que la totalidad de los registros válidos quedaron efectivamente persistidos.