"""
generar_dataset_pruebas.py

Genera uno de los 5 archivos JSON de pruebas con la estructura de NASA POWER.
El usuario elige el caso por consola (1-5).

Casos disponibles:
  1. caso_01_normal.json           → Caso base ideal (todo válido)
  2. caso_02_interpolacion.json    → Huecos pequeños (-999) para interpolar
  3. caso_03_huecos_grandes.json   → Huecos largos que NO deben interpolarse
  4. caso_04_timestamps_faltantes.json → Filas completas eliminadas
  5. caso_05_validacion_fisica.json    → Datos físicamente imposibles

Uso:
    python generar_dataset_pruebas.py
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================
FECHA_INICIO = datetime(2026, 3, 1)
NUM_DIAS = 3
LATITUD = 4.64
LONGITUD = -74.08
ALTITUD = 1790.38

DIRECTORIO_SALIDA = "datos/raw/outputs_nasa"

# Mapeo de número de caso → nombre de archivo
CASOS = {
    "1": "caso_01_normal.json",
    "2": "caso_02_interpolacion.json",
    "3": "caso_03_huecos_grandes.json",
    "4": "caso_04_timestamps_faltantes.json",
    "5": "caso_05_validacion_fisica.json",
}


# ============================================================
# 1. GENERACIÓN DE DATOS BASE FÍSICAMENTE COHERENTES
# ============================================================
def generar_irradiancia_base(hora):
    """Curva solar senoidal (~6am a ~6pm). Máximo ~900 W/m² al mediodía."""
    if 6 <= hora <= 18:
        return 900.0 * math.sin(math.pi * (hora - 6) / 12.0)
    return 0.0


def generar_temperatura_base(hora):
    """Temperatura diurna: mínimo ~16°C madrugada, máximo ~25°C 14h."""
    return 20.0 + 5.0 * math.sin(math.pi * (hora - 5) / 18.0)


def generar_dia_base(fecha):
    """Genera las 24 horas de un día con valores coherentes."""
    datos = {}
    for h in range(24):
        ts = fecha.strftime("%Y%m%d") + f"{h:02d}"
        irr = generar_irradiancia_base(h)
        temp = generar_temperatura_base(h)
        factor_dia = 1.0 + 0.05 * (fecha.day - 1)
        datos[ts] = {
            "ALLSKY_SFC_SW_DWN": round(irr * factor_dia, 2),
            "T2M": round(temp + 0.3 * (fecha.day - 1), 2),
        }
    return datos


def generar_datos_base_completos():
    """Genera los datos base de los 3 días."""
    datos_totales = {}
    for d in range(NUM_DIAS):
        fecha = FECHA_INICIO + timedelta(days=d)
        datos_totales.update(generar_dia_base(fecha))
    return datos_totales


# ============================================================
# 2. INYECCIÓN DE ERRORES POR CASO
# ============================================================
def inyectar_errores_caso_1(datos_totales):
    """Caso 1: Normal. No se inyecta ningún error."""
    return []


def inyectar_errores_caso_2(datos_totales):
    """
    Caso 2: Huecos pequeños (máximo 2 horas consecutivas) para probar
    interpolación. Todos los huecos son interpolables.
    """
    verdad_terreno = []
    FILL = -999.0

    d2 = "20260302"

    # Hueco de 2 horas en irradiancia y temperatura (06:00-07:00)
    for h in ("06", "07"):
        datos_totales[f"{d2}{h}"]["ALLSKY_SFC_SW_DWN"] = FILL
        datos_totales[f"{d2}{h}"]["T2M"] = FILL
        verdad_terreno.append((f"{d2}{h}", "hueco_2h", "debe_interpolarse"))

    # Hueco de 1 hora en temperatura (14:00)
    datos_totales[f"{d2}14"]["T2M"] = FILL
    verdad_terreno.append(("2026030214", "hueco_1h_temp", "debe_interpolarse"))

    # Hueco de 2 horas en irradiancia (10:00-11:00)
    for h in ("10", "11"):
        datos_totales[f"{d2}{h}"]["ALLSKY_SFC_SW_DWN"] = FILL
        verdad_terreno.append((f"{d2}{h}", "hueco_2h_irr", "debe_interpolarse"))

    # Hueco de 1 hora en día 3 (09:00)
    d3 = "20260303"
    datos_totales[f"{d3}09"]["T2M"] = FILL
    datos_totales[f"{d3}09"]["ALLSKY_SFC_SW_DWN"] = FILL
    verdad_terreno.append(("2026030309", "hueco_1h_dia3", "debe_interpolarse"))

    return verdad_terreno


def inyectar_errores_caso_3(datos_totales):
    """
    Caso 3: Huecos grandes (>2 horas) que NO deben interpolarse.
    Permanecen como faltantes.
    """
    verdad_terreno = []
    FILL = -999.0

    d2 = "20260302"

    # Hueco de 5 horas consecutivas (08:00-12:00)
    for h in ("08", "09", "10", "11", "12"):
        datos_totales[f"{d2}{h}"]["ALLSKY_SFC_SW_DWN"] = FILL
        datos_totales[f"{d2}{h}"]["T2M"] = FILL
        verdad_terreno.append((f"{d2}{h}", "hueco_5h", "no_debe_interpolarse"))

    # Hueco de 3 horas en día 3 (14:00-16:00)
    d3 = "20260303"
    for h in ("14", "15", "16"):
        datos_totales[f"{d3}{h}"]["ALLSKY_SFC_SW_DWN"] = FILL
        datos_totales[f"{d3}{h}"]["T2M"] = FILL
        verdad_terreno.append((f"{d3}{h}", "hueco_3h_dia3", "no_debe_interpolarse"))

    # Hueco de 4 horas solo en temperatura día 2 (18:00-21:00)
    for h in ("18", "19", "20", "21"):
        datos_totales[f"{d2}{h}"]["T2M"] = FILL
        verdad_terreno.append((f"{d2}{h}", "hueco_4h_temp", "no_debe_interpolarse"))

    return verdad_terreno


def inyectar_errores_caso_4(datos_totales):
    """
    Caso 4: Timestamps faltantes. Filas completas eliminadas del JSON.
    El pipeline debe reconstruirlas.
    """
    verdad_terreno = []

    # Día 2: eliminar 13:00 y 14:00 (hueco de 2 horas)
    d2 = "20260302"
    del datos_totales[f"{d2}13"]
    del datos_totales[f"{d2}14"]
    verdad_terreno.append(("2026030213", "timestamp_faltante", "reconstruir"))
    verdad_terreno.append(("2026030214", "timestamp_faltante", "reconstruir"))

    # Día 3: eliminar 08:00, 17:00 y 18:00 (timestamps dispersos)
    d3 = "20260303"
    del datos_totales[f"{d3}08"]
    del datos_totales[f"{d3}17"]
    del datos_totales[f"{d3}18"]
    verdad_terreno.append(("2026030308", "timestamp_faltante", "reconstruir"))
    verdad_terreno.append(("2026030317", "timestamp_faltante", "reconstruir"))
    verdad_terreno.append(("2026030318", "timestamp_faltante", "reconstruir"))

    # Día 1: eliminar 22:00 (timestamp aislado)
    d1 = "20260301"
    del datos_totales[f"{d1}22"]
    verdad_terreno.append(("2026030122", "timestamp_faltante", "reconstruir"))

    return verdad_terreno


def inyectar_errores_caso_5(datos_totales):
    """
    Caso 5: Validación física. Datos físicamente imposibles para probar
    todas las alertas y correcciones automáticas.
    """
    verdad_terreno = []

    d2 = "20260302"
    d3 = "20260303"

    # Irradiancia negativa (12:00 día 2)
    datos_totales[f"{d2}12"]["ALLSKY_SFC_SW_DWN"] = -30.0
    verdad_terreno.append(("2026030212", "irr_negativa", "alerta"))

    # Irradiancia > 1400 W/m² (11:00 día 2)
    datos_totales[f"{d2}11"]["ALLSKY_SFC_SW_DWN"] = 11000.0
    verdad_terreno.append(("2026030211", "irr_fuera_rango_alto", "alerta"))

    # Temperatura < 0°C (04:00 día 3)
    datos_totales[f"{d3}04"]["T2M"] = -8.0
    verdad_terreno.append(("2026030304", "temp_bajo_cero", "alerta"))

    # Temperatura > 30°C (13:00 día 2)
    datos_totales[f"{d2}13"]["T2M"] = 48.0
    verdad_terreno.append(("2026030213", "temp_muy_alta", "alerta"))

    # Irradiancia nocturna ALTA (02:00 día 2) → ALERTA CRÍTICA
    datos_totales[f"{d2}02"]["ALLSKY_SFC_SW_DWN"] = 500.0
    verdad_terreno.append(("2026030202", "irr_nocturna_critica", "alerta_critica"))

    # Ruido nocturno pequeño (01:00 día 2) → forzar a 0
    datos_totales[f"{d2}01"]["ALLSKY_SFC_SW_DWN"] = 2.0
    verdad_terreno.append(("2026030201", "ruido_nocturno", "forzar_cero"))

    # Otro caso de ruido nocturno (03:00 día 3)
    datos_totales[f"{d3}03"]["ALLSKY_SFC_SW_DWN"] = 4.0
    verdad_terreno.append(("2026030303", "ruido_nocturno", "forzar_cero"))

    # Irradiancia nocturna ALTA adicional (23:00 día 3)
    datos_totales[f"{d3}23"]["ALLSKY_SFC_SW_DWN"] = 350.0
    verdad_terreno.append(("2026030323", "irr_nocturna_critica", "alerta_critica"))

    # Temperatura extremadamente alta (14:00 día 3)
    datos_totales[f"{d3}14"]["T2M"] = 42.0
    verdad_terreno.append(("2026030314", "temp_muy_alta", "alerta"))

    # Irradiancia ligeramente negativa (15:00 día 3)
    datos_totales[f"{d3}15"]["ALLSKY_SFC_SW_DWN"] = -5.0
    verdad_terreno.append(("2026030315", "irr_negativa", "alerta"))

    return verdad_terreno


# Mapeo de funciones por caso
INYECCIONES = {
    "1": inyectar_errores_caso_1,
    "2": inyectar_errores_caso_2,
    "3": inyectar_errores_caso_3,
    "4": inyectar_errores_caso_4,
    "5": inyectar_errores_caso_5,
}


# ============================================================
# 3. CONSTRUCCIÓN DEL JSON CON ESTRUCTURA NASA POWER
# ============================================================
def construir_json(datos_totales, fecha_inicio, num_dias):
    """Convierte el diccionario plano en la estructura GeoJSON de NASA POWER."""
    timestamps = sorted(datos_totales.keys())
    allsky = {ts: datos_totales[ts]["ALLSKY_SFC_SW_DWN"] for ts in timestamps}
    t2m = {ts: datos_totales[ts]["T2M"] for ts in timestamps}
    fecha_fin = fecha_inicio + timedelta(days=num_dias - 1)

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [LONGITUD, LATITUD, ALTITUD],
        },
        "properties": {
            "parameter": {
                "ALLSKY_SFC_SW_DWN": allsky,
                "T2M": t2m,
            }
        },
        "header": {
            "title": "NASA/POWER Source Native Resolution Hourly Data",
            "api": {"version": "v2.9.5", "name": "POWER Hourly API"},
            "sources": ["MERRA2", "SYN1DEG"],
            "fill_value": -999.0,
            "time_standard": "LST",
            "start": fecha_inicio.strftime("%Y%m%d"),
            "end": fecha_fin.strftime("%Y%m%d"),
        },
        "messages": [],
        "parameters": {
            "ALLSKY_SFC_SW_DWN": {
                "units": "Wh/m^2",
                "longname": "All Sky Surface Shortwave Downward Irradiance",
            },
            "T2M": {
                "units": "C",
                "longname": "Temperature at 2 Meters",
            },
        },
        "times": {"data": 0.121, "process": 0.03},
    }


# ============================================================
# 4. MENÚ DE SELECCIÓN DE CASO
# ============================================================
def seleccionar_caso():
    """Muestra el menú y devuelve el número de caso elegido."""
    print("=" * 60)
    print("GENERADOR DE DATASETS DE PRUEBAS NASA POWER")
    print("=" * 60)
    print("\nSelecciona el caso a generar:\n")
    print("  1. caso_01_normal.json           → Caso base ideal")
    print("  2. caso_02_interpolacion.json    → Huecos pequeños (≤2h)")
    print("  3. caso_03_huecos_grandes.json   → Huecos largos (>2h)")
    print("  4. caso_04_timestamps_faltantes.json → Filas eliminadas")
    print("  5. caso_05_validacion_fisica.json    → Datos imposibles")
    print()

    while True:
        opcion = input("Ingresa el número del caso (1-5): ").strip()
        if opcion in CASOS:
            return opcion
        print("  ⚠ Opción inválida. Debe ser un número del 1 al 5.\n")


# ============================================================
# 5. MAIN
# ============================================================
def main():
    caso = seleccionar_caso()
    nombre_archivo = CASOS[caso]

    ruta_directorio = Path(DIRECTORIO_SALIDA)
    ruta_directorio.mkdir(parents=True, exist_ok=True)
    ruta_archivo = ruta_directorio / nombre_archivo

    print(f"\n{'=' * 60}")
    print(f"Generando caso {caso}: {nombre_archivo}")
    print(f"Ruta de salida: {ruta_archivo.resolve()}")
    print(f"{'=' * 60}\n")

    # Paso 1: datos base coherentes
    datos_totales = generar_datos_base_completos()
    print(f"  - Generados {len(datos_totales)} registros base")

    # Paso 2: inyectar errores según el caso
    inyectar = INYECCIONES[caso]
    verdad_terreno = inyectar(datos_totales)
    print(f"  - Inyectados {len(verdad_terreno)} errores/controlados")

    # Paso 3: construir JSON
    json_final = construir_json(datos_totales, FECHA_INICIO, NUM_DIAS)

    # Paso 4: guardar
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(json_final, f, indent=4)
    print(f"  - Archivo JSON guardado: {ruta_archivo}")

    # Paso 5: resumen
    if verdad_terreno:
        print(f"\n=== RESUMEN DE CONTROLES INYECTADOS (caso {caso}) ===")
        for ts, tipo, detalle in verdad_terreno:
            print(f"  {ts}  |  {tipo:<30}  |  {detalle}")
    else:
        print("\n=== CASO 1: SIN ERRORES INYECTADOS ===")
        print("  Todos los registros son válidos. Curva solar y temperatura normales.")

    # Conteos según el caso
    print(f"\n=== ESTADÍSTICAS DEL ARCHIVO ===")
    print(f"  Registros en JSON (crudo): {len(datos_totales)}")
    print(f"  Registros esperados (3 días × 24h): {NUM_DIAS * 24}")
    if caso == "4":
        faltantes = NUM_DIAS * 24 - len(datos_totales)
        print(f"  Timestamps eliminados: {faltantes}")


if __name__ == "__main__":
    main()