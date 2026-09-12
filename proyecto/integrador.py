import json
import csv
import os
import time
from datetime import datetime
import requests


URL_BASE = "https://appsweb.quantaiot.co"  
EQUIPO = "equipo_Eddy_Irma_TPS"        
     
def buscar_archivo(nombre_archivo):
    if os.path.exists(nombre_archivo):
        return nombre_archivo
    ruta_datos = os.path.join("datos", nombre_archivo)
    if os.path.exists(ruta_datos):
        return ruta_datos
    return None

def cargar_datos():
    registros_raw = []

    ruta_a = buscar_archivo("proveedor_a.json")
    if ruta_a is None:
        print("Aviso: no se encontró proveedor_a.json, se omite esta fuente.")
    else:
        try:
            with open(ruta_a, "r", encoding="utf-8") as file:
                data_a = json.load(file)
            for idx, item in enumerate(data_a.get("records", [])):
                item["_trazabilidad_id"] = f"proveedor_a_{idx + 1}"
                item["_origen_raw"] = "proveedor_a"
                registros_raw.append(item)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Aviso: no se pudo leer proveedor_a.json ({e}), se omite esta fuente.")

    ruta_b = buscar_archivo("proveedor_b.csv")
    if ruta_b is None:
        print("Aviso: no se encontró proveedor_b.csv, se omite esta fuente.")
    else:
        try:
            with open(ruta_b, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file, delimiter=";")
                for idx, row in enumerate(reader):
                    row["_trazabilidad_id"] = f"proveedor_b_{idx + 1}"
                    row["_origen_raw"] = "proveedor_b"
                    registros_raw.append(row)
        except (OSError, csv.Error) as e:
            print(f"Aviso: no se pudo leer proveedor_b.csv ({e}), se omite esta fuente.")

    return registros_raw

def normalizar_registro(raw):
    origen = raw.get("_origen_raw")
    trazabilidad = raw.get("_trazabilidad_id")
    
    try:
        if origen == "proveedor_a":
            station = raw.get("station", {})
            city = station.get("city_name")
            country = station.get("country_code")
            location = raw.get("location", {})
            lat = location.get("lat")
            lon = location.get("lon")
            measurements = raw.get("measurements", {})
            temp_f = measurements.get("temperature_f")
            hum = measurements.get("relative_humidity")
            wind_ms = measurements.get("wind_speed_ms")
            observed_at = raw.get("observed_at")
            
            if not city or not country or lat is None or lon is None:
                return None, "Ubicación incompleta"
            if temp_f is None or temp_f == "N/A" or hum is None or wind_ms is None or not observed_at:
                return None, "Mediciones o fecha nulas"
                
            temp_c = (float(temp_f) - 32.0) * (5.0 / 9.0)
            viento_kmh = float(wind_ms) * 3.6
            fecha_iso = datetime.fromisoformat(observed_at).isoformat()
            
            normalized = {
                "ciudad": str(city).strip(),
                "pais": str(country).strip(),
                "latitud": round(float(lat), 6),
                "longitud": round(float(lon), 6),
                "temperatura_c": round(temp_c, 2),
                "humedad": round(float(hum), 2),
                "viento_kmh": round(viento_kmh, 2),
                "fecha_hora": fecha_iso,
                "origen": "proveedor_a",
                "_trazabilidad_id": trazabilidad
            }
            return normalized, None

        elif origen == "proveedor_b":
            city = raw.get("municipality")
            country = raw.get("country")
            lat = raw.get("latitude_deg")
            lon = raw.get("longitude_deg")
            temp_c = raw.get("temp_celsius")
            hum = raw.get("humidity_pct")
            wind_k = raw.get("wind_kmh")
            m_time = raw.get("measurement_time")
            
            if not city or not country or not lat or not lon or not temp_c or not hum or not wind_k or not m_time:
                return None, "Campos incompletos en CSV"
                
            dt = datetime.strptime(m_time, "%d/%m/%Y %H:%M")
            fecha_iso = dt.isoformat()
            
            normalized = {
                "ciudad": str(city).strip(),
                "pais": str(country).strip(),
                "latitud": round(float(lat), 6),
                "longitud": round(float(lon), 6),
                "temperatura_c": round(float(temp_c), 2),
                "humedad": round(float(hum), 2),
                "viento_kmh": round(float(wind_k), 2),
                "fecha_hora": fecha_iso,
                "origen": "proveedor_b",
                "_trazabilidad_id": trazabilidad
            }
            return normalized, None

    except Exception as e:
        return None, f"Error de transformación: {str(e)}"

def validar_localmente(norm):
    if not norm:
        return False
    if not (-90 <= norm["latitud"] <= 90):
        return False
    if not (-180 <= norm["longitud"] <= 180):
        return False
    if not (0 <= norm["humedad"] <= 100):
        return False
    if norm["viento_kmh"] < 0:
        return False
    if norm["origen"] not in ["proveedor_a", "proveedor_b"]:
        return False
    if not norm["ciudad"] or not norm["pais"]:
        return False
    return True

def enviar_con_reintentos(payload):
    """
    Envía una medición validada a la API mediante HTTP POST.
    Reintenta hasta 3 veces solo en errores 5xx, timeouts o fallas de red.
    """
    endpoint = f"{URL_BASE}/api/v1/mediciones"
    headers = {
        "Content-Type": "application/json",
        "X-Equipo": EQUIPO
    }
    
    # Se remueve la clave interna de trazabilidad para cumplir con el contrato oficial
    data_to_send = {k: v for k, v in payload.items() if not k.startswith("_")}
    
    max_intentos = 3
    intentos = 0
    
    while intentos < max_intentos:
        intentos += 1
        try:
            response = requests.post(endpoint, json=data_to_send, headers=headers, timeout=5)

            # El contrato indica que el body es JSON con info del resultado;
            # se interpreta, pero se tolera si el servidor no devuelve JSON válido.
            try:
                cuerpo = response.json()
            except ValueError:
                cuerpo = None

            # Errores 4xx NO se reintentan automáticamente
            if 400 <= response.status_code < 500:
                return {"exito": False, "status_code": response.status_code, "motivo": "rechazado_api", "respuesta": cuerpo}

            # Éxito (201 Created)
            if response.status_code == 201:
                return {"exito": True, "status_code": response.status_code, "motivo": "aceptado_api", "respuesta": cuerpo}

        except requests.RequestException:
            pass  # Error de conexión o timeout -> reintentar si quedan intentos
            
        if intentos < max_intentos:
            time.sleep(0.5)
            
    return {"exito": False, "status_code": None, "motivo": "error_comunicacion", "respuesta": None}

def consultar_registros_guardados():
    """Consulta final GET a la API institucional."""
    endpoint = f"{URL_BASE}/api/v1/mediciones"
    params = {"equipo": EQUIPO}
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None

def ejecutar_pipeline():
    os.makedirs("salida", exist_ok=True)
    
    datos_crudos = cargar_datos()
    procesados_cnt = len(datos_crudos)
    
    normalizados_list = []
    errores_norm_cnt = 0
    validos_locales = []
    rechazados_locales = []
    detalle_registros = {}  # trazabilidad_id -> resultado del registro

    # 1. Normalización y Validación Local
    for r in datos_crudos:
        tid = r.get("_trazabilidad_id")
        norm, err = normalizar_registro(r)
        if norm:
            normalizados_list.append(norm)
            if validar_localmente(norm):
                validos_locales.append(norm)
                detalle_registros[tid] = {"resultado": "valido_localmente"}
            else:
                rechazados_locales.append(norm)
                detalle_registros[tid] = {"resultado": "rechazado_localmente"}
        else:
            errores_norm_cnt += 1
            detalle_registros[tid] = {"resultado": "error_normalizacion", "motivo": err}
            
    # Guardar evidencia de normalización en salida/normalizadas.json
    with open(os.path.join("salida", "normalizadas.json"), "w", encoding="utf-8") as f:
        json.dump(normalizados_list, f, indent=2, ensure_ascii=False)
        
    # 2. Integración HTTP
    aceptados_api_cnt = 0
    rechazados_api_cnt = 0
    errores_comunicacion_cnt = 0
    
    for reg in validos_locales:
        tid = reg.get("_trazabilidad_id")
        res = enviar_con_reintentos(reg)
        detalle_registros[tid] = {
            "resultado": res["motivo"],
            "status_code": res["status_code"],
            "respuesta_api": res["respuesta"]
        }
        if res["motivo"] == "aceptado_api":
            aceptados_api_cnt += 1
        elif res["motivo"] == "rechazado_api":
            rechazados_api_cnt += 1
        else:
            errores_comunicacion_cnt += 1
            
    # 3. Consulta de Verificación
    consulta_final = consultar_registros_guardados()
    
    # 4. Compilación del Reporte Final en salida/reporte.json
    reporte = {
        "equipo": EQUIPO,
        "resumen": {
            "registros_procesados": procesados_cnt,
            "registros_normalizados": len(normalizados_list),
            "errores_normalizacion": errores_norm_cnt,
            "registros_validos_localmente": len(validos_locales),
            "registros_rechazados_localmente": len(rechazados_locales),
            "registros_enviados": len(validos_locales),
            "registros_aceptados_api": aceptados_api_cnt,
            "registros_rechazados_api": rechazados_api_cnt,
            "errores_comunicacion": errores_comunicacion_cnt
        },
        "consulta_final_api": consulta_final,
        "detalle_por_registro": detalle_registros
    }
    
    with open(os.path.join("salida", "reporte.json"), "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print("--- PIPELINE EJECUTADO ---")
    print(f"Procesados: {procesados_cnt}")
    print(f"Normalizados: {len(normalizados_list)}")
    print(f"Errores de Normalización: {errores_norm_cnt}")
    print(f"Válidos Localmente (Enviados): {len(validos_locales)}")
    print(f"Rechazados Localmente: {len(rechazados_locales)}")
    print(f"Aceptados por API: {aceptados_api_cnt}")
    print(f"Rechazados por API: {rechazados_api_cnt}")
    print(f"Errores de Comunicación: {errores_comunicacion_cnt}")

if __name__ == "__main__":
    ejecutar_pipeline()