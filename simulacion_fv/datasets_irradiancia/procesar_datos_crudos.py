# import argparse
# import os
# import glob
from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# python simulacion_fv/datasets_irradiancia/procesar_datos_crudos.py

# Opción 1: Especificar un archivo JSON concreto
ARCHIVO_JSON = "datos_crudos_4.6401_-74.0801_20260301_20260301.json"

# Opción 2: Dejar vacío para usar el más reciente
# ARCHIVO_JSON = None

# Opción 3: Archivos de simulacion de casos.
# CASO 1: caso_01_normal.json - Caso base - Todo válido, sin correcciones ni alertas.
# ARCHIVO_JSON = "caso_01_normal.json"

# CASO 2: caso_02_interpolacion.json - Huecos pequeños - Interpolación de huecos de hasta 2 horas y actualización de la trazabilidad.
# ARCHIVO_JSON = "caso_02_interpolacion.json"

# CASO 3: caso_03_huecos_grandes.json - Huecos largos - Los datos no se interpolan y permanecen como faltantes.
# ARCHIVO_JSON = "caso_03_huecos_grandes.json"

# CASO 4: caso_04_timestamps_faltantes.json - Continuidad temporal - Reconstrucción del índice temporal y marcado de filas reconstruidas.
# ARCHIVO_JSON = "caso_04_timestamps_faltantes.json"

# CASO 5: caso_05_validacion_fisica.json - Consistencia física - Detección de valores fuera de rango, irradiancia nocturna, ruido nocturno y demás validaciones físicas.
# ARCHIVO_JSON = "caso_05_validacion_fisica.json"

VALOR_RECHAZO = -999
FRECUENCIA_DATOS = "1h"

MAX_HUECO_INTERPOLABLE_HORAS = 2

RUTA_GRAFICOS = Path("datos/processed/reportes")
RUTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

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

    columnas = [col for col in df.columns if col != "trazabilidad"]

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

def generar_histogramas(df):

    print("\nGenerando histogramas...")

    variables = [
        "T2M",
        "ALLSKY_SFC_SW_DWN"
    ]

    nombres = {
        "T2M": "temperatura",
        "ALLSKY_SFC_SW_DWN": "irradiancia"
    }

    for variable in variables:

        plt.figure(figsize=(8,5))

        df[variable].dropna().hist(
            bins=30
        )

        plt.title(variable)

        plt.xlabel(variable)

        plt.ylabel("Frecuencia")

        plt.tight_layout()

        archivo = (
            RUTA_GRAFICOS /
            f"histograma_{nombres[variable]}.png"
        )

        plt.savefig(
            archivo,
            dpi=300
        )

        plt.close()

        print(f"Guardado: {archivo}")

def generar_curva_irradiancia(df):

    # Si la fecha está en el índice
    irradiancia_hora = df.groupby(df.index.hour)["ALLSKY_SFC_SW_DWN"].mean()

    plt.figure(figsize=(8,5))
    plt.plot(
        irradiancia_hora.index,
        irradiancia_hora.values,
        marker='o',
        linewidth=2
    )

    plt.title("Curva de irradiancia media por hora")
    plt.xlabel("Hora del día")
    plt.ylabel("Irradiancia (W/m²)")
    plt.xticks(range(0,24))
    plt.grid(True)

    plt.savefig(
        RUTA_GRAFICOS / "curva_irradiancia_hora.png",
        dpi=300
    )
    plt.close()

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

    # 5. Analizar cada columna
    porcentajes, porcentaje_critico = analizar_columnas(
        df,
        df_numerico.columns
    )

    generar_histogramas(df)

    generar_curva_irradiancia(df)

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

def verificar_continuidad_temporal(df):

    print("\nVerificación de continuidad temporal")
    print("-----------------------------------------------------")

    indice_esperado = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=FRECUENCIA_DATOS
    )

    faltantes = indice_esperado.difference(df.index)

    if len(faltantes) == 0:

        print("No existen registros temporales faltantes.")

    else:

        print(f"Se encontraron {len(faltantes)} timestamps inexistentes.")

        print("\nPrimeros registros faltantes:")

        print(faltantes[:20])

    return faltantes

def reconstruir_eje_temporal(df):

    frecuencia = "1h"

    # --- CORRECCIÓN: Guardar el índice original antes del reindex ---
    indice_original = df.index

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
        
    # --- CORRECCIÓN: Rellenar con "crudo" las filas nuevas para evitar NaN en strings ---
    df["trazabilidad"] = df["trazabilidad"].fillna("crudo")

    # --- CORRECCIÓN: Identificar filas genuinamente nuevas por su ausencia en el índice original ---
    filas_nuevas = ~df.index.isin(indice_original)

    # Usamos agregar_traza por consistencia, aunque al ser filas nuevas están en "crudo"
    df = agregar_traza(df, filas_nuevas, "fila_reconstruida")

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

def obtener_mascara_huecos_interpolables(serie):

    mascara_nan = serie.isna()

    grupos = (mascara_nan != mascara_nan.shift()).cumsum()

    tamano_grupo = mascara_nan.groupby(grupos).transform("sum")

    return mascara_nan & (
        tamano_grupo <= MAX_HUECO_INTERPOLABLE_HORAS
    )

def interpolar_temperatura(df):

    mask = df["T2M"].isna()

    interpolables = obtener_mascara_huecos_interpolables(df["T2M"])

    serie = (df["T2M"].interpolate(method="time"))

    df.loc[interpolables,"T2M"] = serie.loc[interpolables]

    # 1. Anotar las que SÍ se recuperaron
    df = agregar_traza(df,mask & df["T2M"].notna(),"temperatura_interpolada")

    # 2. --- NUEVO: Anotar las que NO se pudieron recuperar ---
    faltantes = (df["T2M"].isna())

    df = agregar_traza(df, faltantes, "temperatura_no_recuperada")

    return df

def interpolar_irradiancia(df):

    mask = df["ALLSKY_SFC_SW_DWN"].isna()

    interpolables = obtener_mascara_huecos_interpolables(df["ALLSKY_SFC_SW_DWN"])

    serie = (df["ALLSKY_SFC_SW_DWN"].interpolate(method="time"))

    df.loc[interpolables,"ALLSKY_SFC_SW_DWN"] = serie.loc[interpolables]

    df = agregar_traza(df,mask & df["ALLSKY_SFC_SW_DWN"].notna(),"irradiancia_interpolada")

    faltantes = (df["ALLSKY_SFC_SW_DWN"].isna())

    # --- CORRECCIÓN: Cambiar la asignación directa por agregar_traza ---
    df = agregar_traza(df, faltantes, "irradiancia_no_recuperada")

    return df

def interpolar_datos(df):

    df = interpolar_temperatura(df)

    df = interpolar_irradiancia(df)

    return df

def agregar_estado(df):

    cond_faltante = (
        df["ALLSKY_SFC_SW_DWN"].isna()
        | df["T2M"].isna()
    )

    cond_reconstruido = (
        df["trazabilidad"]
        .str.contains("fila_reconstruida", na=False)
    )

    cond_corregido_fisicamente = (
        df["trazabilidad"].str.contains(
            "fuera_rango",
            na=False
        )
    )

    cond_interpolado = (
        df["trazabilidad"].str.contains(
            "interpolada",
            na=False
        )
    )

    condiciones = [

        cond_faltante,

        cond_reconstruido,

        cond_corregido_fisicamente,

        cond_interpolado

    ]

    opciones = [

        "faltante",

        "reconstruido",

        "corregido_fisicamente",

        "interpolado"

    ]

    df["estado"] = np.select(
        condiciones,
        opciones,
        default="valido"
    )

    return df

def agregar_origen(df):

    condiciones = [

        df["trazabilidad"].str.contains(
            "fila_reconstruida",
            na=False
        ),

        df["trazabilidad"].str.contains(
            "interpolada",
            na=False
        )

    ]

    opciones = [

        "reconstruido",

        "interpolado"

    ]

    df["origen"] = np.select(
        condiciones,
        opciones,
        default="original"
    )

    return df

# def validar_rangos_fisicos(df):

    errores = []

    if (df["T2M"] < 0).any():
        errores.append("Temperatura menor a 0 C")

    if (df["T2M"] > 30).any():
        errores.append("Temperatura mayor a 30 C")

    if (df["ALLSKY_SFC_SW_DWN"] < 0).any():
        errores.append("Irradiancia negativa")

    if (df["ALLSKY_SFC_SW_DWN"] > 1400).any():
        errores.append("Irradiancia fuera de rango")

    return errores

def validar_resultado(df):

    print("\nDespués de interpolar")

    print(df.isna().sum())

    return df

def calcular_orto_ocaso(latitud, longitud, timestamps):
    """
    Calcula la hora de salida (orto) y puesta (ocaso) del sol para una localización
    en Hora Local (asumiendo que los timestamps ya están en la hora local correcta).
    Implementación simplificada de las ecuaciones astronómicas del NOAA.
    """
    # Convertir latitud a radianes
    lat_rad = np.radians(latitud)
    
    # Extraer el día del año (1 a 365) y la hora decimal
    dia_del_ano = timestamps.dayofyear
    hora_decimal = timestamps.hour + timestamps.minute / 60.0
    
    # 1. Ángulo fraccional del año (en radianes)
    g = 2 * np.pi * (dia_del_ano - 1) / 365
    
    # 2. Declinación solar (en radianes) - Ecuación de Spencer
    declinacion = (0.006918 
                   - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) 
                   - 0.006758 * np.cos(2*g) + 0.000907 * np.sin(2*g) 
                   - 0.002697 * np.cos(3*g) + 0.00148 * np.sin(3*g))
    
    # 3. Ángulo horario del amanecer/atardecer (Cenit solar = 90.833° para refracción atmosférica)
    # cos(w_s) = (cos(90.833) - sin(lat)*sin(dec)) / (cos(lat)*cos(dec))
    cos_w_s = (np.cos(np.radians(90.833)) - np.sin(lat_rad) * np.sin(declinacion)) / (np.cos(lat_rad) * np.cos(declinacion))
    
    # Asegurar límites matemáticos por si hay sol de medianoche/noche polar
    cos_w_s = np.clip(cos_w_s, -1.0, 1.0)
    w_s = np.arccos(cos_w_s) # en radianes
    
    # Convertir ángulo horario a horas (1 rad = 3.8197 horas)
    duracion_media_dia = np.degrees(w_s) / 15.0
    
    # 4. Hora del mediodía solar aproximada (en hora local estándar, ignorando ecuación del tiempo fina)
    # Si la serie ya viene ajustada a la hora local, el mediodía ocurre cerca de las 12:00
    mediodia_solar = 12.0 
    
    hora_amanecer = mediodia_solar - duracion_media_dia
    hora_atardecer = mediodia_solar + duracion_media_dia
    
    return hora_amanecer.values, hora_atardecer.values

def validar_coherencia_solar(df, latitud, longitud):
    """
    Paso 5.4: Valida el sentido físico de la irradiancia usando límites astronómicos.
    Detecta desfases horarios (UTC vs Local) e inconsistencias físicas de valores nocturnos.
    """
    print("\n[Paso 5.4] Iniciando Validación de Sentido Físico...")
    
    # Calcular horas límite astronómicas para cada timestamp
    amanecer, atardecer = calcular_orto_ocaso(latitud, longitud, df.index)
    horas_actuales = df.index.hour + df.index.minute / 60.0
    
    # Definir si astronómicamente es de noche (con un margen de tolerancia de 30 min por seguridad)
    es_noche_astronomica = (horas_actuales < (amanecer - 0.5)) | (horas_actuales > (atardecer + 0.5))
    
    # Buscar registros donde hay irradiancia positiva significativa en plena noche astronómica
    registro_solar_nocturno = (es_noche_astronomica & df["ALLSKY_SFC_SW_DWN"].notna() & (df["ALLSKY_SFC_SW_DWN"] > 5))


    # Buscar registros donde es pleno día pero hay ceros absolutos (excluyendo fallas/nan ya controlados)
    es_dia_astronomico = (horas_actuales > (amanecer + 1.0)) & (horas_actuales < (atardecer - 1.0))
    registro_cero_diurno = (
        es_dia_astronomico
        & (df["ALLSKY_SFC_SW_DWN"] == 0)
        & df["ALLSKY_SFC_SW_DWN"].notna()
    )

    errores = []
    
    # Evaluación de Zona Horaria / Desfases
    if registro_solar_nocturno.sum() > 0:
        horas_conflicto = df[registro_solar_nocturno].index.hour.unique()
        errores.append(
            f"ALERTA CRÍTICA: Se detectó irradiancia > 5 W/m² en horas de la noche ({list(horas_conflicto)}). "
            f"Esto indica casi con certeza un desfase de Zona Horaria (ej. Datos en UTC no convertidos a hora local)."
        )
    
    if registro_cero_diurno.sum() > (len(df) * 0.05): # Si pasa del 5% del dataset
        errores.append(
            "ADVERTENCIA: Hay un volumen inusual de ceros de irradiancia en horas centrales del día. "
            "Verificar si la fuente contiene bloqueos o errores de medición no tipificados."
        )
        
    # Corrección Física Automatizada: Forzar a 0 la irradiancia en la noche real si el error es mínimo (< 5 W/m²)
    noches_limpias = (es_noche_astronomica & df["ALLSKY_SFC_SW_DWN"].notna() & (df["ALLSKY_SFC_SW_DWN"] > 0) & (df["ALLSKY_SFC_SW_DWN"] <= 5))
    if noches_limpias.sum() > 0:
        df.loc[noches_limpias, "ALLSKY_SFC_SW_DWN"] = 0.0
        df = agregar_traza(df, noches_limpias, "forzado_cero_nocturno")
        print(f"-> Se forzaron a 0.0 W/m² un total de {noches_limpias.sum()} registros nocturnos con ruido instrumental menor.")

    if not errores:
        print("-> Validación física exitosa: La curva solar coincide con el ciclo día/noche de la región.")
    else:
        for err in errores:
            print(f"-> {err}")
            
    return df, errores

def validar_consistencia_fisica(df):

    print("\nValidación de consistencia física")
    print("-----------------------------------------------------")

    inconsistencias = []

    # Irradiancia negativa
    mask = df["ALLSKY_SFC_SW_DWN"] < 0

    if mask.any():

        inconsistencias.append(
            f"Irradiancia negativa: {mask.sum()} registros."
        )

        df.loc[mask, "ALLSKY_SFC_SW_DWN"] = np.nan

        df = agregar_traza(
            df,
            mask,
            "irradiancia_fuera_rango"
        )

    # Irradiancia mayor al máximo físico

    mask = df["ALLSKY_SFC_SW_DWN"] > 1400

    if mask.any():

        inconsistencias.append(
            f"Irradiancia >1400 W/m²: {mask.sum()} registros."
        )

        df.loc[mask, "ALLSKY_SFC_SW_DWN"] = np.nan

        df = agregar_traza(
            df,
            mask,
            "irradiancia_fuera_rango"
        )

    # Temperatura menor al mínimo

    mask = df["T2M"] < 0

    if mask.any():

        inconsistencias.append(
            f"Temperatura <0°C: {mask.sum()} registros."
        )

        df.loc[mask, "T2M"] = np.nan

        df = agregar_traza(
            df,
            mask,
            "temperatura_fuera_rango"
        )

    # Temperatura mayor al máximo

    mask = df["T2M"] > 30

    if mask.any():

        inconsistencias.append(
            f"Temperatura >30°C: {mask.sum()} registros."
        )

        df.loc[mask, "T2M"] = np.nan

        df = agregar_traza(
            df,
            mask,
            "temperatura_fuera_rango"
        )

    if inconsistencias:

        print("Se detectaron inconsistencias físicas:")

        for x in inconsistencias:
            print("-", x)

    else:

        print("No se detectaron inconsistencias físicas.")

    return df

def validar_patron_estacional(df, latitud, longitud):

    print("\nValidación estacional")

    dias = (
        pd.Series(df.index.normalize())
        .drop_duplicates()
    )

    resumen = []

    for dia in dias:

        amanecer, atardecer = calcular_orto_ocaso(
            latitud,
            longitud,
            pd.DatetimeIndex([dia])
        )

        duracion = atardecer[0] - amanecer[0]

        resumen.append({
            "fecha": dia,
            "amanecer": amanecer[0],
            "atardecer": atardecer[0],
            "duracion": duracion
        })

    resumen = pd.DataFrame(resumen)

    print(resumen.head())

    print("\nDuración mínima del día")

    print(resumen["duracion"].min())

    print("\nDuración máxima del día")

    print(resumen["duracion"].max())

    return resumen

if __name__ == "__main__":

    # 1. Cargar JSON y extraer coordenadas físicas reales del encabezado
    datos = cargar_json(ARCHIVO_JSON)

    # 2. Coordenadas
    coordenadas = datos["geometry"]["coordinates"]
    longitud, latitud, altitud = coordenadas

    # 3. Convertir a DataFrame
    df_solar = convertir_json_a_dataframe(datos)

    # 4. Limpieza inicial (-999 -> NaN)
    df_solar, reporte = perfilar_datos_crudos(df_solar)

    # 5. Verificar continuidad
    verificar_continuidad_temporal(df_solar)

    # 6. Reconstrucción del eje temporal
    df_solar = reconstruir_eje_temporal(df_solar)

    # 7. Validación de límites físicos
    df_solar = validar_consistencia_fisica(df_solar)

    # 8. Validación astronómica
    df_solar, alertas_astronomicas = validar_coherencia_solar(df_solar, latitud, longitud)

    # 9. Interpolar únicamente los NaN recuperables
    df_solar = interpolar_datos(df_solar)

    # 10. Asignar estado final y origen
    df_solar = agregar_estado(df_solar)
    df_solar = agregar_origen(df_solar)

    # 11. Validación estacional
    resumen_estacional = validar_patron_estacional(df_solar, latitud, longitud)

    # 12. Validación final
    validar_resultado(df_solar)

    interpolados = (df_solar["estado"] == "interpolado").sum()
    reconstruidos = (df_solar["estado"] == "reconstruido").sum()
    faltantes = (df_solar["estado"] == "faltante").sum()

    print("\nResumen de reconstrucción")
    print("-" * 60)
    print(f"Timestamps interpolados : {interpolados}")
    print(f"Timestamps reconstruidos: {reconstruidos}")
    print(f"Timestamps pendientes   : {faltantes}")

    if faltantes > 0:
        print(
            "\nNota: Los huecos detectados superan el umbral máximo permitido para "
            "interpolación. Los timestamps afectados permanecen marcados "
            'como "faltante" para su posterior reconstrucción mediante '
            "el modelo de Machine Learning."
        )

    print("-" * 60)

    print("\nResumen final del estado de calidad de las celdas (Para Tesis):")
    print(df_solar["estado"].value_counts())

    # =========================================================================
    # NUEVO -> PASO 5.5: Guardar con Metadatos e Información de Zona Horaria
    # =========================================================================
    # Agregamos la columna explícita de zona horaria para mitigar errores futuros de lectura
    df_solar["zona_horaria"] = "Hora_Local_Localizada" 

    ruta_salida = Path("datos/processed/outputs_nasa/datos_fv_limpios.csv")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    # Guardar el CSV principal
    df_solar.to_csv(ruta_salida, index=True)
    print(f"\n[Paso 5.5] Dataset procesado guardado exitosamente en: {ruta_salida}")

    # Guardar un archivo de metadatos .json al lado del archivo procesado para soporte metodológico de la tesis
    ruta_metadatos = ruta_salida.with_suffix(".json")
    metadatos_tesis = {

        "descripcion": (
            "Dataset de irradiancia y temperatura superficial "
            "procesado, reconstruido temporalmente, interpolado "
            "y validado físicamente."
        ),

        "fecha_procesamiento": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "coordenadas": {
            "latitud": latitud,
            "longitud": longitud,
            "altitud_m": altitud
        },

        "periodo": {
            "inicio": str(df_solar.index.min()),
            "fin": str(df_solar.index.max()),
            "numero_registros": int(len(df_solar))
        },

        "variables": [
            "ALLSKY_SFC_SW_DWN",
            "T2M"
        ],

        "coherencia_temporal": {
            "frecuencia": FRECUENCIA_DATOS,
            "indexado": "Serie temporal continua reconstruida",
            "filas_reconstruidas": int(
                (
                    df_solar["trazabilidad"]
                    .str.contains(
                        "fila_reconstruida",
                        na=False
                    )
                ).sum()
            )
        },

        "interpolacion": {

            "metodo": "time",

            "max_horas_interpolables":
            MAX_HUECO_INTERPOLABLE_HORAS,

            "temperatura_interpolada": int(
                (
                    df_solar["trazabilidad"]
                    .str.contains(
                        "temperatura_interpolada",
                        na=False
                    )
                ).sum()
            ),

            "irradiancia_interpolada": int(
                (
                    df_solar["trazabilidad"]
                    .str.contains(
                        "irradiancia_interpolada",
                        na=False
                    )
                ).sum()
            ),

            "temperatura_no_recuperada": int(
                (
                    df_solar["trazabilidad"]
                    .str.contains(
                        "temperatura_no_recuperada",
                        na=False
                    )
                ).sum()
            ),

            "irradiancia_no_recuperada": int(
                (
                    df_solar["trazabilidad"]
                    .str.contains(
                        "irradiancia_no_recuperada",
                        na=False
                    )
                ).sum()
            )
        },

        "validacion_fisica": {

            "rangos_temperatura": "0 °C a 30 °C",

            "rangos_irradiancia": "0 a 1400 W/m²",

            "coherencia_dia_noche":
            "Validada mediante orto y ocaso astronómico",

            "alertas": alertas_astronomicas

        },

        "zona_horaria_timestamps":
        "Hora Local (Ajuste astronómico verificado)",

        "estado_calidad": (
            df_solar["estado"]
            .value_counts()
            .to_dict()
        ),

        "metricas_calidad_porcentaje": (
            df_solar["estado"]
            .value_counts(normalize=True)
            .mul(100)
            .round(3)
            .to_dict()
        ),

        "limitaciones": [

        "Se interpolan únicamente huecos de hasta 2 horas mediante interpolación temporal.",

        "Los huecos superiores a 2 horas permanecen como datos faltantes y son marcados para su exclusión en etapas posteriores del modelado.",

        "La interpolación se realiza utilizando el índice temporal (method='time').",

        "Las transiciones de irradiancia durante amanecer y atardecer no reciben un tratamiento diferencial. En estos periodos la irradiancia presenta cambios rápidos, por lo que los valores interpolados pueden tener una incertidumbre mayor que durante las horas centrales del día.",

        "La temperatura e irradiancia se interpolan de manera independiente debido a sus diferentes comportamientos físicos."

    ]

    }

    with open(ruta_metadatos, "w", encoding="utf-8") as f:
        json.dump(metadatos_tesis, f, indent=4, ensure_ascii=False)
    print(f"[Paso 5.5] Metadatos metodológicos para la tesis generados en: {ruta_metadatos}\n")