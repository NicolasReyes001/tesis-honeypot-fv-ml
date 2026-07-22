"""
graficar_resultados.py
================================================================
Paso 17: Visualizar resultados — gráficas clave consolidadas para
la tesis.

Este script no recalcula el modelo ni el MPPT (eso ya lo hacen los
scripts de las Fases 2 y 3) — solo genera/confirma las figuras
finales que van directo al capítulo de resultados:

    1. Curva P-V en condiciones estándar (STC), panel calibrado.
       → reutiliza el modelo validado (Paso 9).
    2. Serie temporal de un día completo (irradiancia + potencia
       MPPT a lo largo del día simulado).
       → nueva en este paso, a partir de datos/processed/potencia_mppt.csv
    3. Comparación potencia ideal vs. MPPT.
       → ya generada en el Paso 13 (comparar_ideal_vs_mppt.py);
       este script verifica que exista y, si no, la genera.

Todas las figuras quedan en tesis/figuras/, listas para insertar en
el documento de la tesis.

Uso:
    python simulacion_fv/pruebas/graficar_resultados.py
================================================================
"""

import sys
import subprocess
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "planta"))

from modelo_diodo_unico import cargar_parametros_desde_yaml  # noqa: E402
from curva_caracteristica import generar_curva_iv_pv, graficar_curva_iv_pv  # noqa: E402

RUTA_YAML_PANEL = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"
RUTA_MPPT = RAIZ_PROYECTO / "datos" / "processed" / "potencia_mppt.csv"
DIR_FIGURAS = RAIZ_PROYECTO / "tesis" / "figuras"

RUTA_FIG_PV_STC = DIR_FIGURAS / "curva_pv_stc_panel_calibrado.png"
RUTA_FIG_SERIE_DIA = DIR_FIGURAS / "serie_temporal_dia_completo.png"
RUTA_FIG_COMPARACION = DIR_FIGURAS / "comparacion_ideal_vs_mppt.png"


# =====================================================================
# FIGURA 1: CURVA P-V EN STC (panel calibrado, Paso 9)
# =====================================================================
def generar_figura_pv_stc():
    print("\n--- [Figura 1/3] Curva P-V en STC (panel calibrado) ---")
    params = cargar_parametros_desde_yaml(RUTA_YAML_PANEL)
    curva = generar_curva_iv_pv(1000.0, 25.0, params)
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    graficar_curva_iv_pv(curva, ruta_guardado=str(RUTA_FIG_PV_STC))
    print(f"  Vmpp={curva.Vmpp:.2f} V, Impp={curva.Impp:.3f} A, Pmpp={curva.Pmpp:.2f} W, "
          f"FF={curva.FF:.3f}")
    print(f"  Guardada en: {RUTA_FIG_PV_STC}")


# =====================================================================
# FIGURA 2: SERIE TEMPORAL DE UN DÍA COMPLETO
# =====================================================================
def generar_figura_serie_dia():
    print("\n--- [Figura 2/3] Serie temporal de un día completo ---")
    if not RUTA_MPPT.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_MPPT}. Ejecute primero "
            "simular_seguimiento_mppt.py (Paso 12)."
        )

    df = pd.read_csv(RUTA_MPPT, index_col="timestamp", parse_dates=True)

    fig, (ax_irr, ax_pot) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    # Panel superior: irradiancia y temperatura (eje secundario)
    ax_irr.plot(df.index, df["irradiancia_wm2"], color="tab:orange", linewidth=1.5,
                label="Irradiancia (W/m²)")
    ax_irr.set_ylabel("Irradiancia (W/m²)", color="tab:orange")
    ax_irr.tick_params(axis="y", labelcolor="tab:orange")
    ax_irr.grid(alpha=0.3)

    ax_temp = ax_irr.twinx()
    ax_temp.plot(df.index, df["temperatura_c"], color="tab:red", linewidth=1.2,
                 linestyle="--", alpha=0.7, label="Temperatura (°C)")
    ax_temp.set_ylabel("Temperatura (°C)", color="tab:red")
    ax_temp.tick_params(axis="y", labelcolor="tab:red")

    ax_irr.set_title("Condiciones ambientales simuladas (irradiancia y temperatura)")

    # Panel inferior: potencia ideal vs. potencia MPPT
    ax_pot.plot(df.index, df["Pmpp_ideal_w"], color="tab:orange", linewidth=1.8,
                label="Potencia ideal (Paso 10)")
    ax_pot.plot(df.index, df["P_mppt_w"], color="tab:blue", linewidth=1.2, alpha=0.85,
                label="Potencia seguida por MPPT (Paso 12, paso_V=0.5V)")
    ax_pot.set_ylabel("Potencia DC (W)")
    ax_pot.set_xlabel("Tiempo")
    ax_pot.set_title("Potencia entregada por el panel a lo largo del día simulado")
    ax_pot.legend(loc="upper right", fontsize=9)
    ax_pot.grid(alpha=0.3)
    ax_pot.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    fig.suptitle(f"Paso 17 — Día simulado completo: {df.index[0].date()}", fontsize=13)
    fig.tight_layout()
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(RUTA_FIG_SERIE_DIA, dpi=150, bbox_inches="tight")
    plt.close(fig)

    energia_ideal_kwh = df["Pmpp_ideal_w"].sum() * (5.0 / 60.0) / 1000.0
    energia_mppt_kwh = df["P_mppt_w"].sum() * (5.0 / 60.0) / 1000.0
    print(f"  Energía ideal: {energia_ideal_kwh:.4f} kWh, "
          f"energía MPPT: {energia_mppt_kwh:.4f} kWh")
    print(f"  Guardada en: {RUTA_FIG_SERIE_DIA}")


# =====================================================================
# FIGURA 3: COMPARACIÓN IDEAL VS. MPPT (verificar que exista, Paso 13)
# =====================================================================
def verificar_o_generar_figura_comparacion():
    print("\n--- [Figura 3/3] Comparación ideal vs. MPPT ---")
    if RUTA_FIG_COMPARACION.exists():
        print(f"  ✓ Ya existe (generada en el Paso 13): {RUTA_FIG_COMPARACION}")
        return

    print("  No existe todavía, generándola con comparar_ideal_vs_mppt.py (Paso 13)...")
    script = RAIZ_PROYECTO / "simulacion_fv" / "inversor" / "comparar_ideal_vs_mppt.py"
    r = subprocess.run([sys.executable, str(script)], cwd=str(RAIZ_PROYECTO),
                        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"comparar_ideal_vs_mppt.py falló:\n{r.stdout}\n{r.stderr}")
    print(f"  ✓ Generada en: {RUTA_FIG_COMPARACION}")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 70)
    print("PASO 17: GRÁFICAS FINALES CONSOLIDADAS PARA LA TESIS")
    print("=" * 70)

    generar_figura_pv_stc()
    generar_figura_serie_dia()
    verificar_o_generar_figura_comparacion()

    print("\n" + "=" * 70)
    print("FIGURAS FINALES EN tesis/figuras/:")
    print("=" * 70)
    for ruta in [RUTA_FIG_PV_STC, RUTA_FIG_SERIE_DIA, RUTA_FIG_COMPARACION]:
        estado = "✓" if ruta.exists() else "✗ FALTA"
        print(f"  {estado} {ruta.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()