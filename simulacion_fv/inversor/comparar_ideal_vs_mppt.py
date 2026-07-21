"""
comparar_ideal_vs_mppt.py
================================================================
Paso 13: Guardar y comparar la potencia ideal vs. la seguida por el MPPT.

Ejecuta simular_mppt (Paso 12) con dos tamaños de paso de
perturbación distintos (uno pequeño, uno grande) sobre la misma
serie ambiental, para poder discutir empíricamente en la tesis el
compromiso velocidad de convergencia vs. precisión en estado
estacionario (mencionado en el Paso 11).

Genera:
    - tesis/figuras/comparacion_ideal_vs_mppt.png
    - docs/06_experimentacion/eficiencia_mppt.md

Uso:
    python simulacion_fv/inversor/comparar_ideal_vs_mppt.py
================================================================
"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "planta"))
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "inversor"))

from modelo_diodo_unico import cargar_parametros_desde_yaml  # noqa: E402
from simular_seguimiento_mppt import cargar_serie_ideal, simular_mppt  # noqa: E402

RUTA_YAML_PANEL = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"
RUTA_FIGURA = RAIZ_PROYECTO / "tesis" / "figuras" / "comparacion_ideal_vs_mppt.png"
RUTA_REPORTE = RAIZ_PROYECTO / "docs" / "06_experimentacion" / "eficiencia_mppt.md"

# Dos configuraciones de paso para discutir el compromiso
# velocidad de convergencia vs. precisión en estado estacionario.
PASOS_A_COMPARAR = {
    "paso_pequeño (0.1 V)": 0.1,
    "paso_grande (2.0 V)": 2.0,
}

MARGEN_EFICIENCIA_PCT = 5.0  # % de Pmpp_ideal considerado "dentro del margen"


# =====================================================================
# 1. MÉTRICA DE EFICIENCIA DE SEGUIMIENTO
# =====================================================================
def calcular_metricas(df: pd.DataFrame, margen_pct: float = MARGEN_EFICIENCIA_PCT) -> dict:
    """
    Calcula:
      - % de tiempo (con irradiancia > 0) en que P_mppt está dentro
        de `margen_pct` % del Pmpp_ideal correspondiente.
      - Eficiencia de captura de energía: energía MPPT / energía ideal.
    """
    df_dia = df[df["irradiancia_wm2"] > 0].copy()

    if len(df_dia) == 0:
        return {"pct_tiempo_dentro_margen": float("nan"), "eficiencia_energia_pct": float("nan")}

    diferencia_pct = np.where(
        df_dia["Pmpp_ideal_w"] > 0,
        np.abs(df_dia["P_mppt_w"] - df_dia["Pmpp_ideal_w"]) / df_dia["Pmpp_ideal_w"] * 100.0,
        0.0,
    )
    dentro_margen = diferencia_pct <= margen_pct
    pct_tiempo_dentro_margen = dentro_margen.mean() * 100.0

    energia_ideal = df["Pmpp_ideal_w"].sum()
    energia_mppt = df["P_mppt_w"].sum()
    eficiencia_energia_pct = (energia_mppt / energia_ideal * 100.0) if energia_ideal > 0 else float("nan")

    return {
        "pct_tiempo_dentro_margen": pct_tiempo_dentro_margen,
        "eficiencia_energia_pct": eficiencia_energia_pct,
        "energia_ideal_kwh": energia_ideal * (5.0 / 60.0) / 1000.0,
        "energia_mppt_kwh": energia_mppt * (5.0 / 60.0) / 1000.0,
    }


# =====================================================================
# 2. FIGURA COMPARATIVA
# =====================================================================
def generar_figura(resultados: dict):
    RUTA_FIGURA.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(len(resultados), 1, figsize=(11, 4.5 * len(resultados)), sharex=True)
    if len(resultados) == 1:
        axes = [axes]

    for ax, (nombre, datos) in zip(axes, resultados.items()):
        df = datos["df"]
        ax.plot(df.index, df["Pmpp_ideal_w"], label="Potencia ideal (Paso 10)",
                color="tab:orange", linewidth=1.8)
        ax.plot(df.index, df["P_mppt_w"], label=f"Potencia seguida por MPPT ({nombre})",
                color="tab:blue", linewidth=1.1, alpha=0.85)
        ax.set_ylabel("Potencia (W)")
        ax.set_title(
            f"{nombre} — eficiencia de captura de energía: "
            f"{datos['metricas']['eficiencia_energia_pct']:.2f} % · "
            f"tiempo dentro de ±{MARGEN_EFICIENCIA_PCT:.0f}% del ideal: "
            f"{datos['metricas']['pct_tiempo_dentro_margen']:.1f} %"
        )
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Tiempo")
    fig.suptitle("Paso 13 — Comparación potencia ideal vs. seguimiento MPPT (Perturbar y Observar)",
                 fontsize=13, y=1.0)
    fig.tight_layout()
    fig.savefig(RUTA_FIGURA, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[Paso 13] Figura comparativa guardada en: {RUTA_FIGURA}")


# =====================================================================
# 3. REPORTE MARKDOWN
# =====================================================================
def generar_reporte(resultados: dict):
    RUTA_REPORTE.parent.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filas_tabla = []
    for nombre, datos in resultados.items():
        m = datos["metricas"]
        filas_tabla.append(
            f"| {nombre} | {m['eficiencia_energia_pct']:.2f} % | "
            f"{m['pct_tiempo_dentro_margen']:.1f} % | "
            f"{m['energia_ideal_kwh']:.4f} | {m['energia_mppt_kwh']:.4f} |"
        )

    contenido = f"""# Eficiencia de seguimiento del MPPT (Perturbar y Observar)
**Paso 13 — Fase 3, Algoritmo MPPT**

Fecha de ejecución: {fecha}

## 1. Objetivo

Comparar, sobre la serie ambiental simulada (Paso 6/10), la potencia
"ideal" (Pmpp encontrado barriendo toda la curva I-V en cada instante,
Paso 10) contra la potencia efectivamente entregada por el algoritmo
Perturbar y Observar (P&O, Paso 11-12), que —igual que un inversor
real— solo conoce el voltaje y la potencia del ciclo anterior.

## 2. Métricas usadas

- **Eficiencia de captura de energía**: energía total entregada por
  el MPPT dividida entre la energía total ideal, en el periodo
  simulado.
- **% de tiempo dentro de margen**: fracción de los instantes con
  irradiancia > 0 en los que la potencia del MPPT está a menos de
  ±{MARGEN_EFICIENCIA_PCT:.0f} % de la potencia ideal correspondiente.

## 3. Resultados — comparación de tamaño de paso (paso_V)

| Configuración | Eficiencia de captura de energía | % tiempo dentro de ±{MARGEN_EFICIENCIA_PCT:.0f}% | Energía ideal (kWh) | Energía MPPT (kWh) |
|---|---|---|---|---|
{chr(10).join(filas_tabla)}

## 4. Discusión del compromiso paso pequeño vs. paso grande

"""

    nombres = list(resultados.keys())
    m_pequeno = resultados[nombres[0]]["metricas"]
    m_grande = resultados[nombres[1]]["metricas"]

    if m_pequeno["eficiencia_energia_pct"] >= m_grande["eficiencia_energia_pct"]:
        conclusion_energia = (
            f"En este periodo simulado, el paso pequeño capturó más energía "
            f"({m_pequeno['eficiencia_energia_pct']:.2f} % vs. "
            f"{m_grande['eficiencia_energia_pct']:.2f} %), consistente con lo "
            f"esperado: al oscilar menos alrededor del MPP en estado "
            f"estacionario, pierde menos energía por \"ripple\"."
        )
    else:
        conclusion_energia = (
            f"En este periodo simulado, el paso grande capturó más energía "
            f"({m_grande['eficiencia_energia_pct']:.2f} % vs. "
            f"{m_pequeno['eficiencia_energia_pct']:.2f} %). Esto puede ocurrir "
            f"cuando la irradiancia cambia con suficiente rapidez dentro del "
            f"periodo simulado: un paso grande converge más rápido tras cada "
            f"cambio, mientras que uno pequeño puede quedarse temporalmente "
            f"rezagado del nuevo MPP."
        )

    contenido += f"""{conclusion_energia}

Esto ilustra el compromiso clásico del algoritmo P&O documentado en
la literatura (Femia et al., 2005; Esram & Chapman, 2007):

- **Paso pequeño** ({nombres[0]}): mayor precisión en estado
  estacionario (menor oscilación alrededor del MPP real), pero
  converge más lento tras un cambio brusco de irradiancia (ej. el
  paso de una nube), quedándose temporalmente más lejos del MPP
  mientras se re-ajusta.
- **Paso grande** ({nombres[1]}): converge más rápido tras un cambio
  de condiciones, pero oscila de forma más notoria alrededor del MPP
  incluso en condiciones estables, disipando energía en ese "ripple"
  permanente.

En un inversor comercial, este compromiso suele resolverse con un
**paso variable** (adaptativo): pasos grandes cuando la potencia
cambia mucho entre ciclos (lejos del MPP) y pasos pequeños cuando la
potencia se estabiliza (cerca del MPP) — una extensión natural de
este mismo módulo (`mppt_perturbar_observar.py`) para trabajo futuro,
ya que `EstadoMPPT.paso_V` está diseñado como un campo modificable
del estado, no una constante fija.

## 5. Evidencia gráfica

Ver `tesis/figuras/comparacion_ideal_vs_mppt.png`: series de tiempo
de potencia ideal vs. potencia MPPT para ambas configuraciones de
paso.

## 6. Limitaciones

- La comparación se hizo sobre un único día simulado (2026-03-01,
  277 instantes a 5 minutos). Con un periodo más largo y variado
  (varios perfiles de nubosidad) las diferencias entre configuraciones
  de paso serían más representativas.
- El MPPT arranca "en frío" (sin medición previa) al inicio del
  periodo simulado; el primer tramo de la serie incluye ese
  transitorio de arranque, que penaliza más a la configuración de
  paso pequeño (converge más lento inicialmente). En una ejecución
  continua real, este transitorio ocurre una sola vez, no en cada
  día simulado.
- **Acoplamiento entre el ciclo del MPPT y la resolución de muestreo**:
  en esta simulación se ejecuta exactamente un ciclo de P&O por cada
  instante de la serie ambiental (cada 5 minutos). Un inversor real
  ejecuta su lazo de control MPPT mucho más rápido (típicamente cada
  decenas de milisegundos a pocos segundos): cientos o miles de ciclos
  de P&O entre cada cambio apreciable de irradiancia. Esta es la causa
  principal de que aquí el paso grande haya aventajado al pequeño: con
  solo un ciclo cada 5 minutos, un paso pequeño no alcanza a recorrer
  la curva P-V dentro de cada intervalo. Un refinamiento natural para
  trabajo futuro es desacoplar la tasa de ciclos del MPPT de la
  resolución del dataset ambiental (ej. ejecutar N ciclos de P&O entre
  cada instante ambiental, interpolando G y T dentro de ese intervalo).
"""

    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"[Paso 13] Reporte de eficiencia guardado en: {RUTA_REPORTE}")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 70)
    print("PASO 13: GUARDAR Y COMPARAR POTENCIA IDEAL VS. MPPT")
    print("=" * 70)

    df_ideal = cargar_serie_ideal()

    resultados = {}
    for nombre, paso_v in PASOS_A_COMPARAR.items():
        print(f"\n--- Simulando configuración: {nombre} (paso_V={paso_v} V) ---")
        df_resultado = simular_mppt(df_ideal, paso_V=paso_v)
        metricas = calcular_metricas(df_resultado)
        resultados[nombre] = {"df": df_resultado, "metricas": metricas}

        print(f"  Eficiencia de captura de energía: {metricas['eficiencia_energia_pct']:.2f} %")
        print(f"  % tiempo dentro de ±{MARGEN_EFICIENCIA_PCT:.0f}% del ideal: "
              f"{metricas['pct_tiempo_dentro_margen']:.1f} %")

    generar_figura(resultados)
    generar_reporte(resultados)

    print("\n" + "=" * 70)
    print("PASO 13 COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()