# import argparse
import json
# import os
# import glob
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# python simulacion_fv/datasets_irradiancia/procesar_datos_crudos.py

# Opción 1: Especificar un archivo JSON concreto
# ARCHIVO_JSON = "datos_crudos_4.64_-74.08_20230322_20230322.json"

# Opción 2: Dejar vacío para usar el más reciente
ARCHIVO_JSON = None


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

    variables_disponibles = list(datos["parameters"].keys())

    fecha_inicio = datos["header"]["start"]
    fecha_fin = datos["header"]["end"]

    primera_variable = variables_disponibles[0]
    numero_registros = len(datos["properties"]["parameter"][primera_variable])

    longitud = datos["geometry"]["coordinates"][0]
    latitud = datos["geometry"]["coordinates"][1]
    altitud = datos["geometry"]["coordinates"][2]

    print(f"Archivo cargado: {ruta_archivo.name}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print(f"Altitud: {altitud} m")
    print(f"Variables disponibles: {variables_disponibles}")
    print(f"Fecha inicial: {fecha_inicio}")
    print(f"Fecha final: {fecha_fin}")
    print(f"Número de registros: {numero_registros}")

    return datos


def convertir_json_a_dataframe(datos):
    parametros = datos["properties"]["parameter"]

    parametros = datos["properties"]["parameter"]

    # Crear el DataFrame directamente
    df = pd.DataFrame(parametros)

    # Convertir el índice (timestamps) a datetime
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")

    # Nombrar el índice
    df.index.name = "timestamp"

    # Ordenar cronológicamente
    df.sort_index(inplace=True)

    print("\nPrimer registro ordenado en el DataFrame:")
    print(df.iloc[0])

    print("\nPrimeras 5 filas:")
    print(df.head())

    print("\nÚltimas 5 filas:")
    print(df.tail())

    print("\nInformación del DataFrame:")
    df.info()

    return df  # Es buena práctica retornar el DataFrame para usarlo luego

def estadisticas_columna(serie):

    total = serie.size
    validos = serie.count()
    invalidos = serie.isna().sum()
    porcentaje = (invalidos / total) * 100

    return total, validos, invalidos, porcentaje

def perfilar_datos_crudos(df):

    # Verificación de valores nulos en el DataFrame (-999).
    valor_rechazo = -999
    porcentaje_aceptado = 5.0       # 5%
    porcentaje_advertencia = 20.0   # 20%
    porcentaje_rechazo = 50.0       # 50%   

    # Contamos cuántas celdas en total en las columnas numéricas tienen el valor de rechazo
    df_numerico = df.select_dtypes(include="number")
    total_celdas = df_numerico.size

    if total_celdas == 0:
            raise ValueError("El DataFrame no contiene datos para evaluar.")

    total_invalidos = (df_numerico == valor_rechazo).sum().sum()
    porcentaje_invalidos = (total_invalidos/total_celdas)*100
    
    print("\n")
    print("Descripción dataframe actual: ")
    print(f"Control de Calidad total: {porcentaje_invalidos:.4f}% de los datos son inválidos ({valor_rechazo}).")

    print("\n") 
    
    if porcentaje_invalidos <= porcentaje_aceptado:
        estado_general = "ACEPTABLE"
        print(f"Estado por porcentaje total: {estado_general}")

    elif porcentaje_invalidos <= porcentaje_advertencia:
        estado_general = "ADVERTENCIA"
        print(f"Estado por porcentaje total: {estado_general}")

    elif porcentaje_invalidos <= porcentaje_rechazo:
        estado_general = "RECHAZO"
        print(f"Estado por porcentaje total: {estado_general}")

    else:
        estado_general = "RECHAZO SEVERO"
        print(f"Estado por porcentaje total: {estado_general}")

    

    print("Conversion de datos invalidados -999 a NaN.")

    df = df.replace(valor_rechazo, np.nan)
    print("\nPrimeras 5 filas del dataframe final")
    print(df.head())

    print("\nÚltimas 5 filas del dataframe final:")
    print(df.tail())

    print("\nInformación del DataFrame del dataframe final:")
    df.info()

    print(f"total de datos: {total_celdas}")
    print("\n")
    print("CONTROL DE CALIDAD.")
    print("------------------------------------------------------------------------------")
    print("Control de calidad total:")

    total_celdas = df.size
    total_validos = df.count().sum()
    puntos_faltantes = df.isna().sum().sum()

    # Filas donde ALLSKY... O T2M (o ambas) sean NaN
    timestamps_faltantes = df.index[df.isna().any(axis=1)]

    # Convertimos el índice de fechas faltantes en un DataFrame formal
    df_faltantes = timestamps_faltantes.to_frame(index=False, name='Fechas Faltantes')
    fecha_min = df_faltantes['Fechas Faltantes'].min()
    fecha_max = df_faltantes['Fechas Faltantes'].max()

    # === CÁLCULO DE HORAS TOTALES CRONOLÓGICAS ===
    # 1. Obtenemos la diferencia exacta en la línea de tiempo real
    diferencia_base = df_faltantes['Fechas Faltantes'].max() - df_faltantes['Fechas Faltantes'].min()
    
    # 2. Le sumamos 1 hora (la frecuencia base) para incluir la duración del último intervalo completo
    tiempo_real_total = diferencia_base + pd.Timedelta(hours=1)
    
    # 3. Convertimos el objeto Timedelta a un número flotante/entero de horas reales transcurridas
    horas_totales = tiempo_real_total.total_seconds() / 3600

    print(f"Datos totales: {total_celdas}")
    print(f"Datos válidos totales: {total_validos}")
    print(f"Datos inválidos totales: {total_invalidos}")
    print(f"datos faltantes: {puntos_faltantes} de {total_celdas}.")
    print(f"porcentaje de datos faltantes: {porcentaje_invalidos:.4f}%")
    print("\n")
    print("Timestamps de datos faltantes.")
    print(df_faltantes)
    print(f"desde {fecha_min} hasta {fecha_max}")
    print(f"Horas totales transcurridas: {horas_totales}")
    print("------------------------------------------------------------------------------")
    # irradiancia.
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
    # Temperatura.
    

    porcentaje_critico = max(porcentajes.values())

    print(f"Porcentaje crítico del sistema: {porcentaje_critico:.4f}%")

    if porcentaje_critico <= porcentaje_aceptado:   
        estado_final = "ACEPTABLE"
        print(f"Estado del sistema global: {estado_final}")

    elif porcentaje_critico <= porcentaje_advertencia:
        estado_final = "ADVERTENCIA"
        print(f"Estado del sistema global: {estado_final}")

    elif porcentaje_critico <= porcentaje_rechazo:
        estado_final = "RECHAZO"
        print(f"Estado del sistema global: {estado_final}")

    else:
        estado_final = "RECHAZO SEVERO"
        print(f"Estado del sistema global: {estado_final}")



    # Cantidad de filas del dataframe.
    numero_filas = len(df.index)
    print(numero_filas)

    # rango temporal real: primer timestamp y último timestamp.
    primer_timestamp = df.index.min()
    ultimo_timestamp = df.index.max()
    print(primer_timestamp)
    print(ultimo_timestamp)



# El flujo de ejecución correcto va aquí dentro
if __name__ == "__main__":
    # 1. Se cargan los datos respetando la configuración inicial (fijo o más reciente)
    datos = cargar_json(ARCHIVO_JSON)

    # 2. Se procesan esos mismos datos en el DataFrame
    df_solar = convertir_json_a_dataframe(datos)

    perfilar_df = perfilar_datos_crudos(df_solar)