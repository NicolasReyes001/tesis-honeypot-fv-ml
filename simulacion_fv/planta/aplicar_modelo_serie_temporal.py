"""
aplicar_modelo_serie_temporal.py
================================================================
Paso 10: Aplicar el modelo del panel a toda la serie temporal.

Recorre el dataset ambiental base (irradiancia + temperatura, con
variabilidad sintética de nubosidad ya aplicada en el Paso 6) y,
para cada instante, calcula el punto de máxima potencia "ideal"
del panel de referencia (Kyocera KC200GT, parámetros calibrados
en el Paso 9) usando el modelo de diodo único validado.

Entrada:
    datos/processed/outputs_nasa/datos_fv_sintetico.csv
    (dataset ambiental con irradiancia sintética y temperatura,
    resolución horaria, salida del Paso 6 -
    generar_variabilidad_nubosidad.py)

Procesamiento adicional de este script:
    - Remuestreo por interpolación temporal de la resolución horaria
      original a la resolución de 5 minutos documentada en
      docs/04_metodologia/diseno_dataset.md ("Resolución temporal de
      la simulación fotovoltaica"), siguiendo el mismo criterio ya
      usado en datos/interim/bogota_20230321_5min.csv.
    - Aplicación del modelo de diodo único punto a punto.

Salida:
    datos/processed/potencia_ideal.csv

Uso:
    python simulacion_fv/planta/aplicar_modelo_serie_temporal.py
================================================================
"""

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modelo_diodo_unico import cargar_parametros_desde_yaml   # noqa: E402
from curva_caracteristica import resumen_punto_operativo       # noqa: E402

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
RUTA_ENTRADA = RAIZ_PROYECTO / "datos" / "processed" / "outputs_nasa" / "datos_fv_sintetico.csv"
RUTA_SALIDA = RAIZ_PROYECTO / "datos" / "processed" / "potencia_ideal.csv"
RUTA_YAML_PANEL = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"

RESOLUCION_OBJETIVO = "5min"   # ver docs/04_metodologia/diseno_dataset.md

# Umbral de irradiancia mínima operativa (W/m²). Por debajo de este valor
# NO se invoca el solver de la curva I-V completa. Dos motivos:
#   1. Físico/ingenieril: los inversores comerciales tienen un umbral de
#      arranque (cut-in irradiance) típico de 5-20 W/m² por debajo del
#      cual no hay seguimiento MPPT activo y la potencia entregada es
#      despreciable frente a la potencia nominal (aquí < 0.2% de 200 Wp).
#   2. Numérico: `calcular_voc_ajustado` en modelo_diodo_unico.py (Paso 7)
#      aproxima Voc como función únicamente de la temperatura (no de la
#      irradiancia). Esa aproximación es razonable cerca de STC, pero a
#      irradiancias muy bajas sobreestima el Voc real, lo que hace que el
#      barrido de voltaje de calcular_curva_iv (Paso 8) se extienda más
#      allá del rango donde el solver de Brent puede acotar la raíz,
#      generando fallos de convergencia (ver RuntimeWarning). Se evita
#      invocar el solver en esa región en lugar de modificar el modelo
#      ya validado del Paso 7/8.
IRRADIANCIA_MINIMA_OPERATIVA_WM2 = 15.0


# =====================================================================
# 1. CARGA Y REMUESTREO DEL DATASET AMBIENTAL
# =====================================================================
def cargar_dataset_ambiental() -> pd.DataFrame:
    if not RUTA_ENTRADA.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset ambiental en: {RUTA_ENTRADA}\n"
            "Ejecute primero generar_variabilidad_nubosidad.py (Paso 6)."
        )

    df = pd.read_csv(RUTA_ENTRADA, index_col="timestamp", parse_dates=True)
    print(f"Dataset ambiental cargado: {RUTA_ENTRADA.name}")
    print(f"  - Registros: {len(df)} (resolución original: horaria)")
    print(f"  - Periodo: {df.index.min()} a {df.index.max()}")
    return df


def remuestrear_a_resolucion_objetivo(df: pd.DataFrame, resolucion: str = RESOLUCION_OBJETIVO) -> pd.DataFrame:
    """
    Interpola irradiancia (ALLSKY_SFC_SW_DWN, ya con variabilidad de
    nubosidad) y temperatura (T2M) a la resolución objetivo mediante
    interpolación temporal, siguiendo el mismo criterio metodológico
    documentado para datos/interim/bogota_20230321_5min.csv.

    El estado de nubosidad (categórico) se propaga hacia adelante
    (forward-fill) en lugar de interpolarse, ya que no tiene sentido
    promediar categorías.
    """
    print(f"\n--- Remuestreando de resolución horaria a {resolucion} ---")

    indice_fino = pd.date_range(start=df.index.min(), end=df.index.max(), freq=resolucion)

    columnas_numericas = ["ALLSKY_SFC_SW_DWN", "T2M"]
    df_num = df[columnas_numericas].reindex(df.index.union(indice_fino))
    df_num = df_num.interpolate(method="time").reindex(indice_fino)

    # La irradiancia no puede ser negativa por artefactos de interpolación
    df_num["ALLSKY_SFC_SW_DWN"] = df_num["ALLSKY_SFC_SW_DWN"].clip(lower=0.0)

    df_categ = df[["estado_nubosidad"]].reindex(df.index.union(indice_fino))
    df_categ = df_categ.ffill().bfill().reindex(indice_fino)

    df_fino = pd.concat([df_num, df_categ], axis=1)
    df_fino.index.name = "timestamp"

    print(f"  - Registros tras remuestreo: {len(df_fino)}")
    return df_fino


# =====================================================================
# 2. APLICACIÓN DEL MODELO PUNTO A PUNTO
# =====================================================================
def aplicar_modelo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada fila del dataset ambiental remuestreado, calcula el
    resumen operativo del panel (Vmpp, Impp, Pmpp, Voc, Isc, FF, eta)
    usando el modelo de diodo único calibrado (Paso 9).
    """
    print("\n--- [Paso 10] Aplicando el modelo de diodo único a toda la serie ---")
    params = cargar_parametros_desde_yaml(RUTA_YAML_PANEL)
    print(f"  Panel: {params.Voc} V / {params.Isc} A (parámetros calibrados, Paso 9)")

    inicio = time.time()
    filas = []
    puntos_no_convergentes_total = 0
    n_bajo_umbral = 0

    # Las advertencias residuales del solver (zona de I≈0 cerca de Voc a muy
    # baja irradiancia, ver docstring de calcular_voc_estimado_gt) se cuentan
    # en vez de imprimirse una por una para no saturar la consola.
    with warnings.catch_warnings(record=True) as w_capturados:
        warnings.simplefilter("always")

        for ts, fila in df.iterrows():
            G = float(fila["ALLSKY_SFC_SW_DWN"])
            T = float(fila["T2M"])

            if G < IRRADIANCIA_MINIMA_OPERATIVA_WM2:
                # Por debajo del umbral operativo: potencia nula, sin invocar
                # el solver (ver justificación en IRRADIANCIA_MINIMA_OPERATIVA_WM2).
                n_bajo_umbral += 1
                filas.append({
                    "timestamp": ts,
                    "irradiancia_wm2": G,
                    "temperatura_c": T,
                    "estado_nubosidad": fila["estado_nubosidad"],
                    "Vmpp": 0.0, "Impp": 0.0, "Pmpp_ideal_w": 0.0,
                    "Voc": 0.0, "Isc": 0.0, "FF": 0.0, "eta": 0.0,
                    "curva_valida": True,
                })
                continue

            resumen = resumen_punto_operativo(G, T, params, refinar_mpp=True)
            puntos_no_convergentes_total += resumen.puntos_no_convergentes

            filas.append({
                "timestamp": ts,
                "irradiancia_wm2": G,
                "temperatura_c": T,
                "estado_nubosidad": fila["estado_nubosidad"],
                "Vmpp": resumen.Vmpp,
                "Impp": resumen.Impp,
                "Pmpp_ideal_w": resumen.Pmpp,
                "Voc": resumen.Voc,
                "Isc": resumen.Isc,
                "FF": resumen.FF,
                "eta": resumen.eta,
                "curva_valida": resumen.curva_valida,
            })

        n_warnings_solver = len(w_capturados)

    duracion = time.time() - inicio
    df_resultado = pd.DataFrame(filas).set_index("timestamp")

    print(f"  - Instantes procesados: {len(df_resultado)}")
    print(f"  - Instantes bajo el umbral operativo ({IRRADIANCIA_MINIMA_OPERATIVA_WM2} W/m², "
          f"potencia forzada a 0): {n_bajo_umbral}")
    print(f"  - Tiempo de cómputo: {duracion:.2f} s "
          f"({duracion / max(len(df_resultado), 1) * 1000:.2f} ms/instante)")
    print(f"  - Puntos de curva no convergentes (acumulado, reportado por el modelo): "
          f"{puntos_no_convergentes_total}")
    if n_warnings_solver > 0:
        print(f"  - Advertencias residuales del solver capturadas: {n_warnings_solver} "
              f"(zona I≈0 cerca de Voc a irradiancia muy baja; no afectan el MPP reportado)")

    return df_resultado


# =====================================================================
# 3. RESUMEN Y VALIDACIÓN DE SENTIDO FÍSICO
# =====================================================================
def validar_resultado(df: pd.DataFrame):
    print("\n--- Validación de sentido físico del resultado ---")

    horas_nocturnas = df[df["irradiancia_wm2"] <= 0.0]
    if len(horas_nocturnas) > 0:
        p_max_noche = horas_nocturnas["Pmpp_ideal_w"].max()
        assert p_max_noche == 0.0, f"Potencia nocturna debería ser 0, se obtuvo {p_max_noche}"
        print(f"  ✓ Potencia = 0 W en los {len(horas_nocturnas)} instantes con irradiancia = 0")

    p_max_global = df["Pmpp_ideal_w"].max()
    potencia_nominal = 200.0  # Wp del panel KC200GT en STC
    print(f"  - Potencia máxima obtenida en la serie: {p_max_global:.2f} W "
          f"(potencia nominal del panel: {potencia_nominal:.0f} Wp)")
    assert p_max_global <= potencia_nominal * 1.02, (
        f"La potencia máxima ({p_max_global:.2f} W) supera la potencia nominal "
        f"del panel más un margen del 2% ({potencia_nominal * 1.02:.2f} W)"
    )
    print("  ✓ La potencia máxima no supera la potencia nominal del panel")

    energia_wh = df["Pmpp_ideal_w"].sum() * (5.0 / 60.0)  # 5 min por muestra -> Wh
    print(f"  - Energía ideal acumulada en el periodo simulado: {energia_wh / 1000.0:.3f} kWh")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 70)
    print("PASO 10: APLICAR EL MODELO A TODA LA SERIE TEMPORAL")
    print("=" * 70)

    df_ambiental = cargar_dataset_ambiental()
    df_fino = remuestrear_a_resolucion_objetivo(df_ambiental)
    df_resultado = aplicar_modelo(df_fino)
    validar_resultado(df_resultado)

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.to_csv(RUTA_SALIDA, index=True)
    print(f"\n[Paso 10] Serie de potencia ideal guardada en: {RUTA_SALIDA}")

    print("\n" + "=" * 70)
    print("RESUMEN DEL PASO 10")
    print("=" * 70)
    print(df_resultado[["irradiancia_wm2", "temperatura_c", "Pmpp_ideal_w"]].describe())


if __name__ == "__main__":
    main()