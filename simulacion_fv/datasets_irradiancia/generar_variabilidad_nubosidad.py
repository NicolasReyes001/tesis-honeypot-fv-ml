"""
añadir_variabilidad_sintetica.py
================================================================
Paso 6: Añadir variabilidad sintética controlada mediante
Cadenas de Markov para simular nubosidad realista.

Este script toma el dataset procesado del Paso 5 (datos_fv_limpios.csv)
y le añade variabilidad sintética a la irradiancia simulando estados
de nubosidad mediante una cadena de Markov de 4 estados.

CORRECCIÓN v2: La cadena de Markov se reinicia cada día calendario
para garantizar comparabilidad entre días.

Uso:
    python simulacion_fv/datasets_irradiancia/añadir_variabilidad_sintetica.py

Salida:
    - datos/processed/outputs_nasa/datos_fv_sintetico.csv
    - datos/processed/outputs_nasa/metadatos_variabilidad.json
    - datos/processed/reportes/variabilidad_*.png
================================================================
"""

import json
import math
import random
import warnings
from collections import Counter  # <-- Subido al inicio (antes estaba duplicado dentro de la función)
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ignorar warnings de matplotlib/pandas que ensucian la salida
warnings.filterwarnings("ignore")

# =====================================================================
# CONFIGURACIÓN GLOBAL (Paso 6.7 - Reproducibilidad)
# =====================================================================
# La semilla se fija ANTES de cualquier decisión aleatoria (Paso 6.3)
SEMILLA_GLOBAL = 42
random.seed(SEMILLA_GLOBAL)
np.random.seed(SEMILLA_GLOBAL)

# Rutas
RUTA_DATASET_PROCESADO = Path("datos/processed/outputs_nasa/datos_fv_limpios.csv")
RUTA_SALIDA_CSV = Path("datos/processed/outputs_nasa/datos_fv_sintetico.csv")
RUTA_SALIDA_METADATOS = Path("datos/processed/outputs_nasa/metadatos_variabilidad.json")
RUTA_GRAFICOS = Path("datos/processed/reportes")
RUTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

# Límites físicos (Paso 6.5)
IRR_MAX_TEORICO = 1400.0  # W/m² - Máximo teórico extraterrestre a nivel del suelo
IRR_MIN_FISICO = 0.0      # W/m² - No existe irradiancia negativa

# =====================================================================
# PASO 6.1 - DEFINICIÓN DE ESTADOS DE LA CADENA DE MARKOV
# =====================================================================
ESTADOS_MARKOV = {
    "despejado": {
        "nombre": "Despejado",
        "atenuacion_min": 0.00,
        "atenuacion_max": 0.10,
        "color": "#FFD700",
        "duracion_esperada_horas": 10.0,
    },
    "parcialmente_nublado": {
        "nombre": "Parcialmente Nublado",
        "atenuacion_min": 0.20,
        "atenuacion_max": 0.50,
        "color": "#F0E68C",
        "duracion_esperada_horas": 6.67,
    },
    "nublado": {
        "nombre": "Nublado",
        "atenuacion_min": 0.60,
        "atenuacion_max": 0.85,
        "color": "#C0C0C0",
        "duracion_esperada_horas": 5.56,
    },
    "muy_nublado": {
        "nombre": "Muy Nublado",
        "atenuacion_min": 0.85,
        "atenuacion_max": 0.95,
        "color": "#808080",
        "duracion_esperada_horas": 5.0,
    },
}

# =====================================================================
# PASO 6.2 - MATRIZ DE TRANSICIÓN
# =====================================================================
ORDEN_ESTADOS = ["despejado", "parcialmente_nublado", "nublado", "muy_nublado"]

MATRIZ_TRANSICION = np.array([
    [0.90, 0.08, 0.02, 0.00],
    [0.05, 0.85, 0.08, 0.02],
    [0.00, 0.10, 0.82, 0.08],
    [0.00, 0.05, 0.15, 0.80],
])

assert np.allclose(MATRIZ_TRANSICION.sum(axis=1), 1.0), \
    "Error: Las filas de la matriz de transición no suman 1.0"

# =====================================================================
# PASO 6.5 - CONFIGURACIÓN DEL RUIDO GAUSSIANO
# =====================================================================
RUIDO_SIGMA_PORCENTUAL = 0.03


# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================

def cargar_dataset_procesado():
    print("\n" + "=" * 70)
    print("PASO 6: AÑADIR VARIABILIDAD SINTÉTICA CONTROLADA")
    print("=" * 70)
    
    if not RUTA_DATASET_PROCESADO.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset procesado en: {RUTA_DATASET_PROCESADO}\n"
            "Ejecute primero procesar_datos_crudos.py"
        )
    
    df = pd.read_csv(RUTA_DATASET_PROCESADO, index_col="timestamp", parse_dates=True)
    print(f"\nDataset cargado: {RUTA_DATASET_PROCESADO.name}")
    print(f"  - Registros: {len(df)}")
    print(f"  - Periodo: {df.index.min()} a {df.index.max()}")
    print(f"  - Columnas: {list(df.columns)}")
    
    return df


def simular_cadena_markov_diaria(n_horas, estado_inicial="despejado"):
    """
    Paso 6.3 - Simula la secuencia de estados para UN día (típicamente 24h).
    """
    estado_a_idx = {estado: i for i, estado in enumerate(ORDEN_ESTADOS)}
    idx_a_estado = {i: estado for i, estado in enumerate(ORDEN_ESTADOS)}
    
    estado_actual = estado_inicial
    secuencia_estados = [estado_actual]
    
    for _ in range(1, n_horas):
        idx_actual = estado_a_idx[estado_actual]
        probabilidades = MATRIZ_TRANSICION[idx_actual]
        idx_siguiente = np.random.choice(len(ORDEN_ESTADOS), p=probabilidades)
        estado_actual = idx_a_estado[idx_siguiente]
        secuencia_estados.append(estado_actual)
    
    return secuencia_estados


def simular_cadena_markov_completa(df):
    """
    Paso 6.3 - Simula la cadena de Markov reiniciándola por cada día calendario.
    
    NOTA: El reinicio ocurre al inicio de cada grupo de día calendario
    (df.index.date). Si el dataset no arranca exactamente a las 00:00,
    el primer "día" tendrá menos de 24 horas y el reinicio ocurrirá en
    la primera hora disponible de ese día, no literalmente a medianoche.
    """
    print(f"\n--- [Paso 6.3] Simulando cadena de Markov con reinicio por día calendario ---")
    print(f"  - Estado inicial diario: {ESTADOS_MARKOV['despejado']['nombre']}")
    print(f"  - Semilla global: {SEMILLA_GLOBAL}")
    
    # Advertencia si el dataset no arranca a las 00:00
    primera_hora = df.index[0].hour
    if primera_hora != 0:
        print(f"  [AVISO] El dataset no arranca a las 00:00 (primera hora: {primera_hora}:00). "
              f"El primer 'día' tendrá menos de 24 horas.")
    
    df_con_dia = df.copy()
    df_con_dia["dia"] = df_con_dia.index.date
    
    dias_unicos = sorted(df_con_dia["dia"].unique())
    print(f"  - Número de días calendario a simular: {len(dias_unicos)}")
    
    secuencia_completa = []
    estadisticas_por_dia = []
    
    for dia in dias_unicos:
        mask_dia = df_con_dia["dia"] == dia
        n_horas_dia = mask_dia.sum()
        
        secuencia_dia = simular_cadena_markov_diaria(n_horas_dia, estado_inicial="despejado")
        secuencia_completa.extend(secuencia_dia)
        
        conteo = Counter(secuencia_dia)
        estadisticas_por_dia.append({
            "dia": str(dia),
            "horas": int(n_horas_dia),
            "distribucion": {estado: int(cantidad) for estado, cantidad in conteo.items()},
            "primera_hora": int(df_con_dia.loc[mask_dia].index[0].hour),
            "ultima_hora": int(df_con_dia.loc[mask_dia].index[-1].hour),
        })
    
    # Estadísticas agregadas
    print(f"\n  Distribución de estados en la secuencia completa:")
    conteo_total = Counter(secuencia_completa)
    n_total = len(secuencia_completa)
    for estado, cantidad in conteo_total.items():
        porcentaje = cantidad * 100 / n_total
        print(f"    - {ESTADOS_MARKOV[estado]['nombre']:25} : {cantidad:4} horas ({porcentaje:5.1f}%)")
    
    print(f"\n  Ejemplo de distribución por día (primeros 3 días):")
    for estadistica in estadisticas_por_dia[:3]:
        print(f"    Día {estadistica['dia']}: {estadistica['distribucion']}")
    
    return secuencia_completa, estadisticas_por_dia


def sortear_factor_atenuacion(estado):
    config = ESTADOS_MARKOV[estado]
    factor = random.uniform(config["atenuacion_min"], config["atenuacion_max"])
    return factor


def aplicar_atenuacion(df, secuencia_estados):
    print(f"\n--- [Paso 6.4] Aplicando atenuación por estado de nubosidad ---")
    
    df = df.copy()
    df["estado_nubosidad"] = secuencia_estados
    df["factor_atenuacion"] = np.nan
    df["irradiancia_atenuada"] = df["ALLSKY_SFC_SW_DWN"].copy()
    
    factor_actual = None
    estado_anterior = None
    
    for i, (timestamp, row) in enumerate(df.iterrows()):
        estado_actual = secuencia_estados[i]
        irradiancia_base = row["ALLSKY_SFC_SW_DWN"]
        
        if estado_actual != estado_anterior:
            factor_actual = sortear_factor_atenuacion(estado_actual)
            estado_anterior = estado_actual
        
        if irradiancia_base > 0 and not np.isnan(irradiancia_base):
            irradiancia_atenuada = irradiancia_base * (1.0 - factor_actual)
            df.at[timestamp, "factor_atenuacion"] = factor_actual
            df.at[timestamp, "irradiancia_atenuada"] = irradiancia_atenuada
        else:
            df.at[timestamp, "factor_atenuacion"] = 0.0
            df.at[timestamp, "irradiancia_atenuada"] = irradiancia_base
    
    print(f"  - Atenuación aplicada en horas diurnas")
    print(f"  - Rango de factores aplicados: "
          f"[{df['factor_atenuacion'].min():.3f}, {df['factor_atenuacion'].max():.3f}]")
    
    return df


def aplicar_ruido_gaussiano(df):
    print(f"\n--- [Paso 6.5] Aplicando ruido gaussiano proporcional ---")
    print(f"  - σ = {RUIDO_SIGMA_PORCENTUAL*100:.1f}% del valor actual")
    print(f"  - Clipping físico: [{IRR_MIN_FISICO}, {IRR_MAX_TEORICO}] W/m²")
    
    df = df.copy()
    df["ruido_aplicado"] = np.nan
    df["irradiancia_sintetica"] = df["irradiancia_atenuada"].copy()
    
    for timestamp, row in df.iterrows():
        irradiancia = row["irradiancia_atenuada"]
        
        if irradiancia > 0 and not np.isnan(irradiancia):
            sigma = irradiancia * RUIDO_SIGMA_PORCENTUAL
            ruido = np.random.normal(loc=0.0, scale=sigma)
            irradiancia_con_ruido = irradiancia + ruido
            irradiancia_con_ruido = np.clip(irradiancia_con_ruido, IRR_MIN_FISICO, IRR_MAX_TEORICO)
            
            df.at[timestamp, "ruido_aplicado"] = ruido
            df.at[timestamp, "irradiancia_sintetica"] = irradiancia_con_ruido
        else:
            df.at[timestamp, "ruido_aplicado"] = 0.0
            df.at[timestamp, "irradiancia_sintetica"] = irradiancia
    
    print(f"  - Rango de ruido aplicado: "
          f"[{df['ruido_aplicado'].min():.2f}, {df['ruido_aplicado'].max():.2f}] W/m²")
    
    return df


def generar_graficos_validacion(df):
    print(f"\n--- [Paso 6.6] Generando gráficos de validación ---")
    
    df["dia"] = df.index.date
    dias_unicos = sorted(df["dia"].unique())
    n_dias_mostrar = min(4, len(dias_unicos))
    dias_seleccionados = dias_unicos[:n_dias_mostrar]
    
    # GRÁFICO 1: Comparación ideal vs sintético por día
    fig, axes = plt.subplots(n_dias_mostrar, 1, figsize=(14, 4 * n_dias_mostrar), sharex=True)
    if n_dias_mostrar == 1:
        axes = [axes]
    
    for idx, dia in enumerate(dias_seleccionados):
        ax = axes[idx]
        df_dia = df[df["dia"] == dia]
        horas = df_dia.index.hour + df_dia.index.minute / 60.0
        
        ax.plot(horas, df_dia["ALLSKY_SFC_SW_DWN"],
                label="Ideal (sin nubosidad)", color="blue", linewidth=2, alpha=0.7)
        ax.plot(horas, df_dia["irradiancia_sintetica"],
                label="Sintético (con Markov)", color="red", linewidth=1.5, alpha=0.8)
        
        colores_estado = {
            "despejado": "#FFD70033",
            "parcialmente_nublado": "#F0E68C33",
            "nublado": "#C0C0C033",
            "muy_nublado": "#80808033",
        }
        for estado, color in colores_estado.items():
            mask = df_dia["estado_nubosidad"] == estado
            if mask.any():
                horas_estado = horas[mask]
                if len(horas_estado) > 0:
                    ax.axvspan(horas_estado.min(), horas_estado.max(),
                              alpha=0.3, color=color, label=estado if idx == 0 else None)
        
        ax.set_title(f"Día: {dia} - Irradiancia Ideal vs Sintética", fontsize=12, fontweight="bold")
        ax.set_ylabel("Irradiancia (W/m²)")
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 24)
    
    axes[-1].set_xlabel("Hora del día")
    plt.tight_layout()
    ruta_grafico1 = RUTA_GRAFICOS / "variabilidad_comparacion_dias.png"
    plt.savefig(ruta_grafico1, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  - Gráfico guardado: {ruta_grafico1}")
    
    # GRÁFICO 2: Distribución de estados
    fig, ax = plt.subplots(figsize=(10, 6))
    conteo_estados = df["estado_nubosidad"].value_counts()
    colores = [ESTADOS_MARKOV[estado]["color"] for estado in conteo_estados.index]
    ax.bar(conteo_estados.index, conteo_estados.values, color=colores, edgecolor="black")
    ax.set_title("Distribución de Estados de Nubosidad en el Dataset Sintético",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Estado de Nubosidad")
    ax.set_ylabel("Número de horas")
    ax.grid(axis="y", alpha=0.3)
    
    total = len(df)
    for i, (estado, cantidad) in enumerate(conteo_estados.items()):
        porcentaje = cantidad * 100 / total
        ax.text(i, cantidad + 0.5, f"{porcentaje:.1f}%",
                ha="center", va="bottom", fontweight="bold")
    plt.tight_layout()
    ruta_grafico2 = RUTA_GRAFICOS / "variabilidad_distribucion_estados.png"
    plt.savefig(ruta_grafico2, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  - Gráfico guardado: {ruta_grafico2}")
    
    # GRÁFICO 3: Histograma de factores de atenuación
    fig, ax = plt.subplots(figsize=(10, 6))
    factores_validos = df["factor_atenuacion"].dropna()
    ax.hist(factores_validos, bins=30, color="steelblue", edgecolor="black", alpha=0.7)
    ax.set_title("Distribución de Factores de Atenuación Aplicados",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Factor de Atenuación (0 = sin atenuación, 1 = atenuación total)")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    ruta_grafico3 = RUTA_GRAFICOS / "variabilidad_histograma_atenuacion.png"
    plt.savefig(ruta_grafico3, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  - Gráfico guardado: {ruta_grafico3}")


def guardar_dataset_con_metadatos(df, estadisticas_por_dia):
    """
    Paso 6.7 - Guarda el dataset final y los metadatos de reproducibilidad.
    """
    print(f"\n--- [Paso 6.7] Guardando dataset y metadatos de reproducibilidad ---")
    
    df_final = df[[
        "ALLSKY_SFC_SW_DWN",
        "T2M",
        "estado_nubosidad",
        "factor_atenuacion",
        "irradiancia_atenuada",
        "ruido_aplicado",
        "irradiancia_sintetica",
    ]].copy()
    
    # Renombrado: la columna original pasa a ser "irradiancia_ideal"
    # y la sintética pasa a ser la nueva ALLSKY_SFC_SW_DWN
    # (compatibilidad con el código de la Fase 2 - modelado ML)
    df_final.rename(columns={
        "ALLSKY_SFC_SW_DWN": "irradiancia_ideal",
        "irradiancia_sintetica": "ALLSKY_SFC_SW_DWN"
    }, inplace=True)
    
    RUTA_SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(RUTA_SALIDA_CSV, index=True)
    print(f"  - Dataset sintético guardado: {RUTA_SALIDA_CSV}")
    
    # =================================================================
    # METADATOS DE REPRODUCIBILIDAD
    # =================================================================
    metadatos = {
        "descripcion": (
            "Dataset de irradiancia sintética generado mediante cadena de Markov "
            "de 4 estados para simular nubosidad realista. Incluye atenuación "
            "variable y ruido gaussiano proporcional."
        ),
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reproducibilidad": {
            "semilla_global": SEMILLA_GLOBAL,
            "libreria_random": "Python random + NumPy",
            "nota": "Fijar random.seed() y np.random.seed() con esta semilla "
                    "antes de ejecutar para reproducir exactamente el mismo dataset"
        },
        "cadena_markov": {
            "estados": {
                estado: {
                    "nombre": config["nombre"],
                    "atenuacion_min": config["atenuacion_min"],
                    "atenuacion_max": config["atenuacion_max"],
                    "duracion_esperada_horas": config["duracion_esperada_horas"],
                }
                for estado, config in ESTADOS_MARKOV.items()
            },
            "matriz_transicion": {
                "filas": "estado_actual",
                "columnas": "estado_siguiente",
                "orden_estados": ORDEN_ESTADOS,
                "valores": MATRIZ_TRANSICION.tolist(),
                "validacion_filas_suman_1": bool(
                    np.allclose(MATRIZ_TRANSICION.sum(axis=1), 1.0)
                ),
            },
            "estado_inicial": "despejado",
            "estrategia_simulacion": "reinicio_por_dia_calendario",
            "justificacion": (
                "La cadena de Markov se reinicia al inicio de cada grupo de día "
                "calendario (df.index.date) en estado 'despejado' para garantizar "
                "comparabilidad entre simulaciones de distintos días. Cada día es "
                "una simulación independiente de nubosidad. Si el dataset no cubre "
                "el día completo (ej. arranca a las 06:00), el reinicio ocurre en "
                "la primera hora disponible de ese día, no literalmente a las 00:00."
            ),
        },
        "ruido_gaussiano": {
            "metodo": "normal(0, sigma)",
            "sigma_porcentual": RUIDO_SIGMA_PORCENTUAL,
            "sigma_absoluto_formula": "sigma = irradiancia_actual * 0.03",
            "justificacion": (
                "El ruido se escala proporcionalmente al valor actual para evitar "
                "efectos desproporcionados al amanecer (irradiancia baja) vs mediodía (alta)"
            ),
        },
        "limites_fisicos": {
            "irradiancia_minima": IRR_MIN_FISICO,
            "irradiancia_maxima": IRR_MAX_TEORICO,
            "unidad": "W/m²",
            "nota": "Clipping aplicado después de añadir ruido. El límite superior de 1400 W/m² "
                    "es un valor físico general; una mejora futura sería calcular el máximo teórico "
                    "por instante basado en la geometría solar (orto/ocaso)."
        },
        "estadisticas_dataset": {
            "total_registros": int(len(df)),
            "periodo": {
                "inicio": str(df.index.min()),
                "fin": str(df.index.max()),
            },
            "distribucion_estados": {
                estado: int(cantidad)
                for estado, cantidad in df["estado_nubosidad"].value_counts().items()
            },
            "factor_atenuacion": {
                "media": float(df["factor_atenuacion"].mean()),
                "mediana": float(df["factor_atenuacion"].median()),
                "min": float(df["factor_atenuacion"].min()),
                "max": float(df["factor_atenuacion"].max()),
            },
            "ruido_aplicado": {
                "media": float(df["ruido_aplicado"].mean()),
                "std": float(df["ruido_aplicado"].std()),
                "min": float(df["ruido_aplicado"].min()),
                "max": float(df["ruido_aplicado"].max()),
            },
        },
        "estadisticas_diarias": estadisticas_por_dia,  # <-- NUEVO: persistencia día a día
        "limitaciones": [
            "La cadena de Markov asume que el estado de nubosidad en una hora "
            "depende únicamente del estado de la hora anterior (propiedad de Markov de primer orden).",
            "Los rangos de atenuación son fijos por estado, pero el factor específico "
            "se sortea aleatoriamente dentro del rango en cada entrada al estado.",
            "El ruido gaussiano es independiente en cada hora (no tiene correlación temporal).",
            "No se modelan eventos extremos como tormentas eléctricas o niebla densa "
            "que podrían requerir estados adicionales en la cadena de Markov.",
            "La temperatura (T2M) no se modifica en este paso; solo la irradiancia "
            "recibe variabilidad sintética.",
            "La cadena se reinicia por cada día calendario, lo que implica que no hay "
            "persistencia meteorológica entre días (un día muy nublado no aumenta la "
            "probabilidad de que el siguiente día también lo sea).",
            "El límite superior de clipping (1400 W/m²) es constante; no varía según "
            "la hora del día ni el ángulo solar como lo haría un cálculo astronómico preciso.",
            "Si el dataset de entrada no cubre días completos (ej. arranca a las 06:00), "
            "el primer 'día' tendrá menos de 24 horas y el reinicio ocurrirá en la primera "
            "hora disponible, no literalmente a las 00:00."
        ],
    }
    
    with open(RUTA_SALIDA_METADATOS, "w", encoding="utf-8") as f:
        json.dump(metadatos, f, indent=4, ensure_ascii=False)
    print(f"  - Metadatos guardados: {RUTA_SALIDA_METADATOS}")
    
    return df_final


# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================

def main():
    df = cargar_dataset_procesado()
    
    # Paso 6.3: Simular cadena de Markov con reinicio por día calendario
    secuencia_estados, estadisticas_por_dia = simular_cadena_markov_completa(df)
    
    # Paso 6.4: Aplicar atenuación
    df = aplicar_atenuacion(df, secuencia_estados)
    
    # Paso 6.5: Aplicar ruido gaussiano
    df = aplicar_ruido_gaussiano(df)
    
    # Paso 6.6: Validación visual
    generar_graficos_validacion(df)
    
    # Paso 6.7: Guardar dataset y metadatos
    df_final = guardar_dataset_con_metadatos(df, estadisticas_por_dia)
    
    print("\n" + "=" * 70)
    print("RESUMEN FINAL DEL PASO 6")
    print("=" * 70)
    print(f"Dataset sintético generado: {RUTA_SALIDA_CSV.name}")
    print(f"Metadatos de reproducibilidad: {RUTA_SALIDA_METADATOS.name}")
    print(f"Gráficos de validación: {RUTA_GRAFICOS / 'variabilidad_*.png'}")
    print(f"\nPara reproducir este dataset exactamente:")
    print(f"  1. Usar la semilla: {SEMILLA_GLOBAL}")
    print(f"  2. Ejecutar: random.seed({SEMILLA_GLOBAL}) y np.random.seed({SEMILLA_GLOBAL})")
    print(f"  3. Ejecutar este script con la misma configuración")
    print(f"\nCORRECCIÓN v2: La cadena de Markov se reinicia al inicio de cada día")
    print(f"calendario en estado 'despejado', garantizando comparabilidad entre días.")
    print("=" * 70)
    
    return df_final


if __name__ == "__main__":
    df_sintetico = main()