# Análisis de Integración y Normalización de Datos

## 1. Mapeo y Correspondencia de Contratos

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

## 2. Heterogeneidad de las Fuentes de Datos

* **Estructuras de formato:** El Proveedor A utiliza una estructura JSON anidada (`station`, `location`, `measurements`), mientras que el Proveedor B utiliza un archivo plano CSV delimitado por punto y coma (`;`).
* **Unidades de medida:** 
  * Temperatura: Proveedor A entrega grados Fahrenheit (°F), mientras que Proveedor B entrega grados Celsius (°C).
  * Viento: Proveedor A entrega metros por segundo (m/s), mientras que Proveedor B entrega kilómetros por hora (km/h).
* **Formatos de fecha y hora:** Proveedor A utiliza estándar ISO 8601 con zona horaria (`YYYY-MM-DDTHH:MM:SS-05:00`), mientras que Proveedor B utiliza formato de texto local (`DD/MM/YYYY HH:MM`).

---

## 3. Conversiones de Unidades y Transformaciones

* **Temperatura (°F a °C):** Se aplicó la fórmula `(F - 32) * (5 / 9)` para los datos del Proveedor A.
* **Velocidad del viento (m/s a km/h):** Se aplicó la fórmula `ms * 3.6` para los datos del Proveedor A.
* **Fechas a ISO 8601:**
  * Proveedor A: Se parseó usando `datetime.fromisoformat()` para validar su estructura estándar.
  * Proveedor B: Se convirtió desde la cadena `DD/MM/YYYY HH:MM` a formato ISO 8601 estandarizado utilizando `datetime.strptime()`.

---

## 4. Gestión de Errores e Inconsistencias

* **Campos nulos o ausentes:** Se descartaron registros con cadenas vacías, valores `N/A` o campos faltantes en la estructura original.
* **Formatos inválidos:** Se capturaron excepciones en la conversión de tipos (strings no convertibles a `float` o cadenas de fecha corruptas).
* **Fuera de rango en validación local:** Se filtraron registros cuyas coordenadas estaban fuera de rango (`latitud` fuera de [-90, 90] o `longitud` fuera de [-180, 180]), valores de `humedad` negativos o mayores a 100%, o `viento_kmh` menor a 0.

---

## 5. Validación Local vs. Validación del Servidor (API)

* **Validación Local:** Es determinista y rápida. Se encarga de garantizar que la estructura matemática y sintáctica del dato sea correcta antes de realizar llamados por red. Ahorra ancho de banda y procesamiento.
* **Validación del Servidor (API):** Es la fuente de verdad del sistema. Valida lógica de negocio más compleja, duplicidad de datos, autorización y reglas institucionales que la aplicación cliente desconoce.
* **Diferencia de rol:** La validación local prepara y limpia los datos en el cliente; la validación remota protege la integridad del sistema central.