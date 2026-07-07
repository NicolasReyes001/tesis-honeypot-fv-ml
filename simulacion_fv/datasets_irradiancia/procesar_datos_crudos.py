# import argparse
import json
# import os
# import glob
from datetime import datetime
from pathlib import Path
import pandas as pd

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

    registros = []
    # Usamos una variable cualquiera para sacar los timestamps (ej. la primera disponible)
    primera_var = list(parametros.keys())[0]
    timestamps = list(parametros[primera_var].keys())

    for timestamp in timestamps:
        registro = {"timestamp": timestamp}

        for variable in parametros:
            registro[variable] = parametros[variable][timestamp]

        registros.append(registro)

    # Convertir YYYYMMDDHH a objeto datetime real
    for registro in registros:
        registro["timestamp"] = datetime.strptime(
            registro["timestamp"], "%Y%m%d%H"
        )

    df = pd.DataFrame(registros)
    df = df.sort_values(by="timestamp")
    df.set_index("timestamp", inplace=True)
    
    # Cambiamos 50 por None para que NUNCA recorte los datos, sin importar cuántos sean
    pd.set_option('display.max_rows', None)

    print("\nPrimer registro ordenado en el DataFrame:")
    print(df.iloc[0])
    print("\nDataFrame Completo:")
    print(df)

    return df  # Es buena práctica retornar el DataFrame para usarlo luego

def perfilar_datos_crudos(df):

    # Verificación de valores nulos en el DataFrame (-999).
    valor_rechazo = -999
    porcentaje_aceptado = 0.05
    porcentaje_advertencia = 0.2
    porcentaje_rechazo = 0.5

    # Contamos cuántas celdas en total en las columnas numéricas tienen el valor de rechazo
    df_numerico = df.select_dtypes(include="number")
    total_celdas = df_numerico.size

    if total_celdas == 0:
            raise ValueError("El DataFrame no contiene datos para evaluar.")

    total_invalidos = (df_numerico == valor_rechazo).sum().sum()
    porcentaje_invalidos = total_invalidos / total_celdas

    total_validos = total_celdas - total_invalidos    
    print(f"Control de Calidad: {porcentaje_invalidos:.4%} de los datos son inválidos ({valor_rechazo}).")
    
    print(f"Datos válidos: {total_validos}")
    print(f"Datos inválidos: {total_invalidos}")

    if porcentaje_invalidos <= porcentaje_aceptado:
        estado = "ACEPTABLE"

    elif porcentaje_invalidos <= porcentaje_advertencia:
        estado = "ADVERTENCIA"

    elif porcentaje_invalidos <= porcentaje_rechazo:
        estado = "RECHAZO"

    else:
        estado = "RECHAZO SEVERO"

    print(f"Estado: {estado}")
        

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