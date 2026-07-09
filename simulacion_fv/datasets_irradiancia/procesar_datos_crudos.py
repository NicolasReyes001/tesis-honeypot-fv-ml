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
ARCHIVO_JSON = "documento_prueba.json"

# Opción 2: Dejar vacío para usar el más reciente
# ARCHIVO_JSON = None

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

    total_invalidos = (
        df_numerico.eq(VALOR_RECHAZO)
        .sum()
        .sum()
    )

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

    columnas = df.columns

    faltantes = {}

    # Todos los timestamps
    faltantes["TODAS"] = timestamps_faltantes.to_frame(
        index=False,
        name="Fechas Faltantes"
    )

    # Timestamps por columna
    for col in columnas:
        faltantes[col] = df.index[df[col].isna()].to_frame(
            index=False,
            name="Fechas Faltantes"
        )

    resultado = {}

    for nombre, df_faltante in faltantes.items():

        # Si no hay faltantes
        if df_faltante.empty:

            resultado[nombre] = {
                "faltantes": df_faltante,
                "huecos": pd.DataFrame(
                    columns=[
                        "fecha_inicio",
                        "fecha_fin",
                        "cantidad",
                        "horas"
                    ]
                )
            }

            continue

        # Ordenar cronológicamente
        df_faltante = df_faltante.sort_values(
            "Fechas Faltantes"
        ).copy()

        # Diferencia entre timestamps consecutivos
        df_faltante["diff"] = (
            df_faltante["Fechas Faltantes"].diff()
        )

        # Nuevo grupo cuando la diferencia deja de ser de 1 hora
        df_faltante["grupo"] = (
            df_faltante["diff"] != pd.Timedelta(hours=1)
        ).cumsum()

        # Resumen por grupo
        huecos = (
            df_faltante.groupby("grupo")
            .agg(
                fecha_inicio=("Fechas Faltantes", "min"),
                fecha_fin=("Fechas Faltantes", "max"),
                cantidad=("Fechas Faltantes", "count"),
            )
        )

        huecos["horas"] = (
            (huecos["fecha_fin"] - huecos["fecha_inicio"])
            .dt.total_seconds() / 3600
        ) + 1

        resultado[nombre] = {
            "faltantes": df_faltante,
            "huecos": huecos
        }

    return resultado

def analizar_columnas(df, columnas):

    # Analizar únicamente las variables de interés.
    porcentajes = {}

    for columna in columnas:

        print(f"Columna: {columna}")

        total, validos, invalidos, porcentaje = estadisticas_columna(
            df[columna]
        )

        porcentajes[columna] = porcentaje

        print(f"Datos totales: {total}")
        print(f"Datos válidos totales: {validos}")
        print(f"Datos inválidos totales: {invalidos}")
        print(f"Datos faltantes: {invalidos} de {total}")
        print(f"Porcentaje de datos faltantes: {porcentaje:.4f}%")
        print("------------------------------------------------------------------------------")

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

    df["trazabilidad"] = np.where(
        df[df_numerico.columns].isna().any(axis=1),
        "faltante_original",
        "crudo"
    )
    print("Dataframe completo con trazabilidad.")
    print(df)

    # 3. Estadísticas generales del DataFrame limpio
    df_numerico = df.select_dtypes(include="number")

    puntos_faltantes = df_numerico.isna().sum().sum()

    total_validos = df_numerico.size - puntos_faltantes 

    print("\nCONTROL DE CALIDAD")
    print("------------------------------------------------------------------------------")
    print(f"Datos totales: {total_celdas}")
    print(f"Datos válidos: {total_validos}")
    print(f"Datos inválidos originales: {total_invalidos}")
    print(f"Datos faltantes: {puntos_faltantes} de {total_celdas}")
    print(f"Porcentaje de datos faltantes: {porcentaje_invalidos:.4f}%")

    # 4. Analizar fechas faltantes
    fechas = analizar_fechas_faltantes(df)

    print("\nHuecos de datos faltantes:")

    for nombre, info in fechas.items():

        print(f"\n=== {nombre} ===")

        if info["huecos"].empty:
            print("No existen datos faltantes.")
            continue

        for i, (_, hueco) in enumerate(info["huecos"].iterrows(), start=1):

            print(f"Hueco {i}")
            print(f"Desde : {hueco['fecha_inicio']}")
            print(f"Hasta : {hueco['fecha_fin']}")
            print(f"Horas : {int(hueco['horas'])}")
            print(f"Cantidad de registros : {hueco['cantidad']}")
            print("-" * 40)

    print("------------------------------------------------------------------------------")

    # 5. Analizar cada columna
    porcentajes, porcentaje_critico = analizar_columnas(
        df,
        df_numerico.columns
    )

    print(f"Porcentaje crítico del sistema: {porcentaje_critico:.4f}%")

    estado_original = clasificar_porcentaje(porcentaje_critico)

    print(f"Estado calidad datos originales: {estado_original}")

    # 6. Información temporal del DataFrame
    numero_filas = len(df.index)
    primer_timestamp = df.index.min()
    ultimo_timestamp = df.index.max()

    print(f"Número de filas: {numero_filas}")
    print(f"Primer timestamp: {primer_timestamp}")
    print(f"Último timestamp: {ultimo_timestamp}")

    # 7. Construcción del reporte
    reporte = construir_reporte(
        estado_original,
        porcentaje_critico,
        numero_filas,
        primer_timestamp,
        ultimo_timestamp
    )

    return df, reporte

def reconstruir_eje_temporal(df):

    frecuencia = "1h"

    indice_completo = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=frecuencia
    )

    df = df.reindex(indice_completo)

    df.index.name = "timestamp"

    # Crear trazabilidad si aún no existe
    if "trazabilidad" not in df.columns:
        df["trazabilidad"] = "crudo"

    filas_reconstruidas = (
        df[
            ["ALLSKY_SFC_SW_DWN", "T2M"]
        ].isna().all(axis=1)
    )

    df.loc[
        filas_reconstruidas,
        "trazabilidad"
    ] = "fila_reconstruida"

    return df

def agregar_traza(df, mascara, texto):

    df.loc[mascara, "trazabilidad"] = (
        df.loc[mascara, "trazabilidad"]
        .apply(
            lambda x: x + "|" + texto
            if texto not in x
            else x
        )
    )

    return df

def interpolar_temperatura(df):

    mask = df["T2M"].isna()


    df["T2M"] = (
        df["T2M"]
        .interpolate(
            method="time",
            limit=2,
            limit_direction="both"
        )
    )

    df = agregar_traza(
        df,
        mask & df["T2M"].notna(),
        "temperatura_interpolada"
    )

    return df

def interpolar_irradiancia(df):

    mask = df["ALLSKY_SFC_SW_DWN"].isna()


    df["ALLSKY_SFC_SW_DWN"] = (
        df["ALLSKY_SFC_SW_DWN"]
        .interpolate(
            method="time",
            limit=2,
            limit_direction="both"
        )
    )


    interpolados = (
        mask &
        df["ALLSKY_SFC_SW_DWN"].notna()
    )


    df = agregar_traza(
        df,
        interpolados,
        "irradiancia_interpolada"
    )


    faltantes = (
        df["ALLSKY_SFC_SW_DWN"].isna()
    )


    df.loc[
        faltantes,
        "trazabilidad"
    ] = "irradiancia_no_recuperada"


    return df

def interpolar_datos(df):

    df = interpolar_temperatura(df)

    df = interpolar_irradiancia(df)

    return df

def agregar_estado(df):

    estado = []

    for _, fila in df.iterrows():

        traz = fila["trazabilidad"]

        irradiancia = fila["ALLSKY_SFC_SW_DWN"]

        temperatura = fila["T2M"]


        if pd.isna(irradiancia) or pd.isna(temperatura):
            estado.append("faltante")


        elif "interpolada" in traz:
            estado.append("interpolado")


        elif "reconstruida" in traz or "fila_reconstruida" in traz:
            estado.append("reconstruido")


        else:
            estado.append("valido")


    df["estado"] = estado

    return df

def validar_rangos_fisicos(df):

    errores = []

    if (df["T2M"] < 0).any():
        errores.append("Temperatura menor a -50 C")

    if (df["T2M"] > 30).any():
        errores.append("Temperatura mayor a 60 C")

    if (df["ALLSKY_SFC_SW_DWN"] < 0).any():
        errores.append("Irradiancia negativa")

    if (df["ALLSKY_SFC_SW_DWN"] > 1400).any():
        errores.append("Irradiancia fuera de rango")

    return errores

def validar_resultado(df):

    print("\nDespués de interpolar")

    print(df.isna().sum())

    return df

# El flujo de ejecución correcto va aquí dentro
if __name__ == "__main__":

    # 1. Cargar JSON
    datos = cargar_json(ARCHIVO_JSON)

    # 2. Convertir a DataFrame
    df_solar = convertir_json_a_dataframe(datos)

    # 3. Perfilado y limpieza inicial (-999 -> NaN)
    df_solar, reporte = perfilar_datos_crudos(df_solar)

    # 4. Reconstrucción del eje temporal
    df_solar = reconstruir_eje_temporal(df_solar)

    # 5. Interpolación
    df_solar = interpolar_datos(df_solar)

    df_solar = agregar_estado(df_solar)

    errores_fisicos = validar_rangos_fisicos(df_solar)

    print("\nValidación física")

    if errores_fisicos:
        for error in errores_fisicos:
            print(error)
    else:
        print("Datos dentro de rangos físicos")

    print(df_solar.tail(30))

    print(
        df_solar["estado"]
        .value_counts()
    )

    # 6. Validación final
    validar_resultado(df_solar)

    print("\nReporte del sistema")
    print(reporte)

    # Guardar dataset procesado

    ruta_salida = Path(
        "datos/processed/outputs_nasa/datos_fv_limpios.csv"
    )

    ruta_salida.parent.mkdir(
        exist_ok=True
    )

    df_solar.to_csv(
        ruta_salida
    )

    print(
        f"\nDataset guardado en: {ruta_salida}"
    )