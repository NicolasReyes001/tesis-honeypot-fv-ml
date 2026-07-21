"""
simular_seguimiento_mppt.py
================================================================
Paso 12: Simular la convergencia del MPPT en el tiempo.

Ejecuta el algoritmo P&O (Paso 11) ciclo a ciclo sobre TODA la serie
ambiental (la misma que ya se usó en el Paso 10), alimentándolo en
cada instante con las condiciones (G, T) reales de ese instante.

A diferencia del Paso 10 (que en cada instante calcula el Pmpp IDEAL
barriendo toda la curva, como si el inversor "viera" toda la curva
I-V), aquí el MPPT solo conoce, en cada ciclo, el voltaje y la
potencia del ciclo anterior — igual que un inversor real. Esto
introduce un retraso de seguimiento (tracking lag) y oscilación
alrededor del MPP que el Paso 10 no puede capturar.

Se registran en paralelo, para cada instante:
    - Pmpp_ideal_w: la potencia ideal (Paso 10, referencia)
    - P_mppt_w: la potencia efectivamente entregada por el MPPT
    - V_mppt: el voltaje de operación decidido por el MPPT

Entrada:
    datos/processed/potencia_ideal.csv (Paso 10)

Salida:
    datos/processed/potencia_mppt.csv

Uso:
    python simulacion_fv/inversor/simular_seguimiento_mppt.py [--paso-v 0.5]
================================================================
"""

import sys
import argparse
from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "planta"))
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "inversor"))

from modelo_diodo_unico import cargar_parametros_desde_yaml   # noqa: E402
from mppt_perturbar_observar import EstadoMPPT, estado_inicial, paso_mppt  # noqa: E402

RUTA_ENTRADA = RAIZ_PROYECTO / "datos" / "processed" / "potencia_ideal.csv"
RUTA_SALIDA = RAIZ_PROYECTO / "datos" / "processed" / "potencia_mppt.csv"
RUTA_YAML_PANEL = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"

PASO_V_DEFECTO = 0.5  # V - paso de perturbación por defecto


def cargar_serie_ideal() -> pd.DataFrame:
    if not RUTA_ENTRADA.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_ENTRADA}. Ejecute primero "
            "aplicar_modelo_serie_temporal.py (Paso 10)."
        )
    df = pd.read_csv(RUTA_ENTRADA, index_col="timestamp", parse_dates=True)
    print(f"Serie ideal cargada: {len(df)} instantes "
          f"({df.index.min()} a {df.index.max()})")
    return df


def simular_mppt(df: pd.DataFrame, paso_V: float = PASO_V_DEFECTO) -> pd.DataFrame:
    """
    Recorre la serie temporal ciclo a ciclo, aplicando paso_mppt en
    cada instante con las condiciones ambientales de ESE instante.
    """
    params = cargar_parametros_desde_yaml(RUTA_YAML_PANEL)
    estado = estado_inicial(params, paso_V=paso_V)

    print(f"\n--- [Paso 12] Simulando seguimiento MPPT (paso_V = {paso_V} V) ---")
    print(f"  Estado inicial: V_operacion = {estado.V_operacion:.3f} V")

    filas = []
    for ts, fila in df.iterrows():
        G = float(fila["irradiancia_wm2"])
        T = float(fila["temperatura_c"])

        # V_operacion ANTES de este ciclo es el voltaje que se aplica
        # y se mide en este instante.
        V_aplicado = estado.V_operacion
        estado, P_medida = paso_mppt(estado, G, T, params)

        filas.append({
            "timestamp": ts,
            "irradiancia_wm2": G,
            "temperatura_c": T,
            "Pmpp_ideal_w": float(fila["Pmpp_ideal_w"]),
            "V_mppt": V_aplicado,
            "P_mppt_w": P_medida,
        })

    df_resultado = pd.DataFrame(filas).set_index("timestamp")
    print(f"  - Instantes simulados: {len(df_resultado)}")
    return df_resultado


def main():
    parser = argparse.ArgumentParser(description="Paso 12: simular seguimiento MPPT")
    parser.add_argument("--paso-v", type=float, default=PASO_V_DEFECTO,
                         help="Paso de perturbación en voltios (default: %(default)s)")
    parser.add_argument("--salida", type=str, default=str(RUTA_SALIDA),
                         help="Ruta del CSV de salida")
    args = parser.parse_args()

    print("=" * 70)
    print("PASO 12: SIMULAR LA CONVERGENCIA DEL MPPT EN EL TIEMPO")
    print("=" * 70)

    df_ideal = cargar_serie_ideal()
    df_resultado = simular_mppt(df_ideal, paso_V=args.paso_v)

    ruta_salida = Path(args.salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.to_csv(ruta_salida, index=True)
    print(f"\n[Paso 12] Serie de potencia MPPT guardada en: {ruta_salida}")

    energia_ideal_wh = df_resultado["Pmpp_ideal_w"].sum() * (5.0 / 60.0)
    energia_mppt_wh = df_resultado["P_mppt_w"].sum() * (5.0 / 60.0)
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Energía ideal:  {energia_ideal_wh / 1000.0:.4f} kWh")
    print(f"  Energía MPPT:   {energia_mppt_wh / 1000.0:.4f} kWh")
    if energia_ideal_wh > 0:
        print(f"  Eficiencia de captura de energía: "
              f"{energia_mppt_wh / energia_ideal_wh * 100.0:.2f} %")


if __name__ == "__main__":
    main()