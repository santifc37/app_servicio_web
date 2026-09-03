import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"


estudiantes_transformados = []

with open(RUTA_CSV, mode="r", encoding="utf-8") as archivo_csv:
    lector = csv.DictReader(archivo_csv)

    for fila in lector:
        activo_bool = fila["activo"].strip().lower() in ("true", "1", "si", "sí")

        estudiante = {
            "id": fila["codigo"],
            "nombre_completo": f"{fila['nombre']} {fila['apellido']}",
            "semestre": int(fila["semestre"]),
            "promedio": float(fila["promedio"]),
            "estado": "Activo" if activo_bool else "Inactivo",
        }
        estudiantes_transformados.append(estudiante)


RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"

def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)


serializar_estudiantes(RUTA_JSON, estudiantes_transformados)


def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)


print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")