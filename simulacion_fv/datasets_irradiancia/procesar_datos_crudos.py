# import argparse
# import os
# import glob
# from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import numpy as np

# python simulacion_fv/datasets_irradiancia/procesar_datos_crudos.py

# Opción 1: Especificar un archivo JSON concreto
# ARCHIVO_JSON = "datos_crudos_4.64_-74.08_20230322_20230322.json"

# Opción 2: Dejar vacío para usar el más reciente
ARCHIVO_JSON = None

VALOR_RECHAZO = -999

def cargar_json(nombre_archivo=None):

    ruta_base = Path("datos/raw/outputs_nasa")

    # Caso 1: El usuario indicó un archivo
    if nombre_archivo:
        ruta_archivo = ruta_base / nombre_archivo

        if not ruta_archivo.exists():
            raise FileNotFoundError(
                f"El archivo '{nombre_archivo}' no existe en '{ruta_base}'."
            )

    # Caso 2: Cargar el archivo más reciente
    else:
        archivos = list(ruta_base.glob("*.json"))

        if not archivos:
            raise FileNotFoundError(
                f"No se encontraron archivos JSON en '{ruta_base}'."
            )

        ruta_archivo = max(archivos, key=lambda archivo: archivo.stat().st_mtime)

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    parameters = datos["properties"]["parameter"]
    header = datos["header"]
    geometry = datos["geometry"]
    coordenadas = geometry["coordinates"]

    variables_disponibles = list(parameters.keys())

    fecha_inicio = header["start"]
    fecha_fin = header["end"]

    primera_variable = variables_disponibles[0]
    numero_registros = len(parameters[primera_variable])

    longitud, latitud, altitud = coordenadas

    print(f"Archivo cargado: {ruta_archivo.name}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print(f"Altitud: {altitud} m")
    print(f"Variables disponibles: {variables_disponibles}")
    print(f"Fecha inicial: {fecha_inicio}")
    print(f"Fecha final: {fecha_fin}")
    print(f"Número de registros: {numero_registros}")

    return datos

def mostrar_resumen(df, titulo=""):

    print(f"\n{titulo}")

    print("\nPrimeras filas:")
    print(df.head())

    print("\nÚltimas filas:")
    print(df.tail())

    print("\nInformación:")
    df.info()

def convertir_json_a_dataframe(datos):
    parameters = datos["properties"]["parameter"]

    # Crear el DataFrame directamente
    df = pd.DataFrame(parameters)

    # Convertir el índice (timestamps) a datetime
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")

    # Nombrar el índice
    df.index.name = "timestamp"

    # Ordenar cronológicamente
    if not df.index.is_monotonic_increasing:
        df.sort_index(inplace=True)

    mostrar_resumen(df, "DataFrame original")

    return df  # Es buena práctica retornar el DataFrame para usarlo luego

def estadisticas_columna(serie):

    total = len(serie)

    invalidos = serie.isna().sum()

    validos = total - invalidos

    porcentaje = invalidos * 100 / total

    return total, validos, invalidos, porcentaje

def clasificar_porcentaje(
        porcentaje,
        aceptable=5,
        advertencia=20,
        rechazo=50):

    if porcentaje <= aceptable:
        return "ACEPTABLE"

    elif porcentaje <= advertencia:
        return "ADVERTENCIA"

    elif porcentaje <= rechazo:
        return "RECHAZO"

    return "RECHAZO SEVERO"

def evaluar_calidad_global(df):

    df_numerico = df.select_dtypes(include="number")

    total_celdas = df_numerico.size

    if total_celdas == 0:
        raise ValueError("El DataFrame no contiene datos para evaluar.")

    total_invalidos = (df_numerico == VALOR_RECHAZO).sum().sum()

    porcentaje_invalidos = total_invalidos * 100 / total_celdas

    estado = clasificar_porcentaje(porcentaje_invalidos)

    return (
        df_numerico,
        total_celdas,
        total_invalidos,
        porcentaje_invalidos,
        estado
    )

def reemplazar_valores_invalidos(df, columnas):

    df[columnas] = df[columnas].replace(
        VALOR_RECHAZO,
        np.nan
    )

    mostrar_resumen(
        df,
        "DataFrame después de reemplazar -999"
    )

    return df

def analizar_fechas_faltantes(df):

    timestamps_faltantes = df.index[df.isna().any(axis=1)]

    df_faltantes = timestamps_faltantes.to_frame(
        index=False,
        name="Fechas Faltantes"
    )

    if df_faltantes.empty:

        return {
            "faltantes": df_faltantes,
            "fecha_min": None,
            "fecha_max": None,
            "horas": 0
        }

    fecha_min = df_faltantes["Fechas Faltantes"].min()
    fecha_max = df_faltantes["Fechas Faltantes"].max()

    horas_totales = (
        (fecha_max - fecha_min).total_seconds()/3600
    ) + 1

    return {
        "faltantes": df_faltantes,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,
        "horas": horas_totales
    }

def analizar_columnas(df):

     # irradiancia y temperatura.
    porcentajes = {}
    for columna in df.columns:

        print(f"Columna: {columna}")

        total, validos, invalidos, porcentaje = estadisticas_columna(df[columna])

        porcentajes[columna] = porcentaje

        print(f"Datos totales: {total}")
        print(f"Datos válidos totales: {validos}")
        print(f"Datos inválidos totales: {invalidos}")
        print(f"Datos faltantes: {invalidos} de {total}")
        print(f"Porcentaje de datos faltantes: {porcentaje:.4f}%")
        print("------------------------------------------------------------------------------")
    # porcentaje critico.
    
    porcentaje_critico = max(porcentajes.values())

    return porcentajes, porcentaje_critico

def construir_reporte(
    estado,
    porcentaje,
    filas,
    inicio,
    fin
):
    return {
        "estado": estado,
        "porcentaje": float(porcentaje),
        "filas": int(filas),
        "inicio": inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "fin": fin.strftime("%Y-%m-%d %H:%M:%S")
    }

def perfilar_datos_crudos(df):

    # 1. Evaluar la calidad global del DataFrame
    (
        df_numerico,
        total_celdas,
        total_invalidos,
        porcentaje_invalidos,
        estado_general
    ) = evaluar_calidad_global(df)

    print("\nDescripción del DataFrame actual:")
    print(
        f"Control de calidad total: "
        f"{porcentaje_invalidos:.4f}% de los datos son inválidos ({VALOR_RECHAZO})."
    )
    print(f"Estado general: {estado_general}\n")

    # 2. Reemplazar los valores inválidos por NaN
    print("Conversión de datos invalidados (-999) a NaN.")
    df = reemplazar_valores_invalidos(df, df_numerico.columns)

    # 3. Estadísticas generales del DataFrame limpio
    nan_mask = df.isna()

    puntos_faltantes = nan_mask.sum().sum()

    total_validos = df.size - puntos_faltantes

    print("\nCONTROL DE CALIDAD")
    print("------------------------------------------------------------------------------")
    print(f"Datos totales: {total_celdas}")
    print(f"Datos válidos: {total_validos}")
    print(f"Datos inválidos originales: {total_invalidos}")
    print(f"Datos faltantes: {puntos_faltantes} de {total_celdas}")
    print(f"Porcentaje de datos faltantes: {porcentaje_invalidos:.4f}%")

    # 4. Analizar fechas faltantes
    fechas = analizar_fechas_faltantes(df)

    print("\nTimestamps de datos faltantes:")
    print(fechas["faltantes"])

    if fechas["fecha_min"] is not None:
        print(f"Desde: {fechas['fecha_min']}")
        print(f"Hasta: {fechas['fecha_max']}")
        print(f"Horas totales transcurridas: {fechas['horas']}")
    else:
        print("No existen datos faltantes.")

    print("------------------------------------------------------------------------------")

    # 5. Analizar cada columna
    porcentajes, porcentaje_critico = analizar_columnas(df)

    print(f"Porcentaje crítico del sistema: {porcentaje_critico:.4f}%")

    estado_final = clasificar_porcentaje(porcentaje_critico)
    print(f"Estado final del sistema: {estado_final}")

    # 6. Información temporal del DataFrame
    numero_filas = len(df.index)
    primer_timestamp = df.index.min()
    ultimo_timestamp = df.index.max()

    print(f"Número de filas: {numero_filas}")
    print(f"Primer timestamp: {primer_timestamp}")
    print(f"Último timestamp: {ultimo_timestamp}")

    # 7. Construcción del reporte
    return construir_reporte(
        estado_final,
        porcentaje_critico,
        numero_filas,
        primer_timestamp,
        ultimo_timestamp
    )

# El flujo de ejecución correcto va aquí dentro
if __name__ == "__main__":
    # 1. Se cargan los datos respetando la configuración inicial (fijo o más reciente)
    datos = cargar_json(ARCHIVO_JSON)

    # 2. Se procesan esos mismos datos en el DataFrame
    df_solar = convertir_json_a_dataframe(datos)

    reporte = perfilar_datos_crudos(df_solar)

    print("\n reporte del sistema.")
    print(reporte)