"""
test_pipeline_integracion.py
================================================================
Paso 16 (Fase 5): Prueba de integración end-to-end.

A diferencia de `simulacion_fv/pruebas/test_modelo_diodo.py` (pruebas
UNITARIAS del modelo matemático en aislamiento), esta prueba verifica
que TODO el pipeline de simulación —desde el dataset ambiental de la
Fase 1 hasta la interfaz de lectura de la Fase 4— corre de principio
a fin sin errores, y que los datos son consistentes entre etapas.

Pipeline verificado (en este orden):
    Fase 1 (ya generado): datos/processed/outputs_nasa/datos_fv_sintetico.csv
    Fase 2, Paso 9:  simulacion_fv/pruebas/validacion_modelo_stc.py
    Fase 2, Paso 10: simulacion_fv/planta/aplicar_modelo_serie_temporal.py
    Fase 3, Paso 12: simulacion_fv/inversor/simular_seguimiento_mppt.py
    Fase 4, Paso 15: simulacion_fv/planta/interfaz_estado_actual.py

Uso:
    python tests/simulacion/test_pipeline_integracion.py
================================================================
"""

import sys
import subprocess
from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "planta"))

RUTA_AMBIENTAL = RAIZ_PROYECTO / "datos" / "processed" / "outputs_nasa" / "datos_fv_sintetico.csv"
RUTA_IDEAL = RAIZ_PROYECTO / "datos" / "processed" / "potencia_ideal.csv"
RUTA_MPPT = RAIZ_PROYECTO / "datos" / "processed" / "potencia_mppt.csv"
RUTA_YAML = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"


def _correr_script(ruta_script: Path, args=None) -> subprocess.CompletedProcess:
    """Ejecuta un script del pipeline como subproceso, tal como lo haría
    el usuario desde la línea de comandos, y captura su salida."""
    cmd = [sys.executable, str(ruta_script)] + (args or [])
    return subprocess.run(cmd, cwd=str(RAIZ_PROYECTO), capture_output=True, text=True)


# =====================================================================
# ETAPA 0: PRECONDICIÓN — dataset ambiental de la Fase 1 debe existir
# =====================================================================
def test_precondicion_dataset_ambiental():
    print("\n[Etapa 0] Precondición: dataset ambiental de la Fase 1")
    assert RUTA_AMBIENTAL.exists(), (
        f"No se encontró {RUTA_AMBIENTAL}. Este test asume que la Fase 1 "
        "(Pasos 4-6) ya se ejecutó y el dataset ambiental existe."
    )
    df = pd.read_csv(RUTA_AMBIENTAL)
    assert len(df) > 0, "El dataset ambiental está vacío"
    print(f"  ✓ Dataset ambiental encontrado: {len(df)} registros")


# =====================================================================
# ETAPA 1: FASE 2 — VALIDACIÓN + APLICACIÓN DEL MODELO
# =====================================================================
def test_fase2_validacion_y_aplicacion():
    print("\n[Etapa 1] Fase 2 (Pasos 9-10): validación + aplicación del modelo")

    r = _correr_script(RAIZ_PROYECTO / "simulacion_fv" / "pruebas" / "validacion_modelo_stc.py")
    assert r.returncode == 0, (
        f"validacion_modelo_stc.py terminó con error (código {r.returncode}).\n"
        f"STDOUT:\n{r.stdout[-2000:]}\nSTDERR:\n{r.stderr[-2000:]}"
    )
    print("  ✓ validacion_modelo_stc.py (Paso 9) corrió sin errores")

    r = _correr_script(RAIZ_PROYECTO / "simulacion_fv" / "planta" / "aplicar_modelo_serie_temporal.py")
    assert r.returncode == 0, (
        f"aplicar_modelo_serie_temporal.py terminó con error (código {r.returncode}).\n"
        f"STDOUT:\n{r.stdout[-2000:]}\nSTDERR:\n{r.stderr[-2000:]}"
    )
    print("  ✓ aplicar_modelo_serie_temporal.py (Paso 10) corrió sin errores")

    assert RUTA_IDEAL.exists(), f"No se generó {RUTA_IDEAL}"
    df_ideal = pd.read_csv(RUTA_IDEAL)
    assert len(df_ideal) > 0, "potencia_ideal.csv está vacío"
    assert (df_ideal["Pmpp_ideal_w"] >= 0).all(), "Pmpp_ideal_w tiene valores negativos"
    assert df_ideal["Pmpp_ideal_w"].max() <= 200.0 * 1.02, (
        "Pmpp_ideal_w supera la potencia nominal del panel (200 Wp) + margen"
    )
    print(f"  ✓ potencia_ideal.csv generado y físicamente coherente ({len(df_ideal)} filas)")


# =====================================================================
# ETAPA 2: FASE 3 — SIMULACIÓN DEL MPPT
# =====================================================================
def test_fase3_simulacion_mppt():
    print("\n[Etapa 2] Fase 3 (Paso 12): simulación del MPPT")

    r = _correr_script(RAIZ_PROYECTO / "simulacion_fv" / "inversor" / "simular_seguimiento_mppt.py")
    assert r.returncode == 0, (
        f"simular_seguimiento_mppt.py terminó con error (código {r.returncode}).\n"
        f"STDOUT:\n{r.stdout[-2000:]}\nSTDERR:\n{r.stderr[-2000:]}"
    )
    print("  ✓ simular_seguimiento_mppt.py (Paso 12) corrió sin errores")

    assert RUTA_MPPT.exists(), f"No se generó {RUTA_MPPT}"
    df_mppt = pd.read_csv(RUTA_MPPT)
    df_ideal = pd.read_csv(RUTA_IDEAL)

    assert len(df_mppt) == len(df_ideal), (
        f"potencia_mppt.csv ({len(df_mppt)} filas) y potencia_ideal.csv "
        f"({len(df_ideal)} filas) deberían tener el mismo número de instantes"
    )
    assert (df_mppt["P_mppt_w"] >= 0).all(), "P_mppt_w tiene valores negativos"
    assert (df_mppt["V_mppt"] >= 0).all(), "V_mppt tiene valores negativos"

    # La energía capturada por el MPPT nunca debería superar la ideal
    # (el MPPT no puede "inventar" potencia que la curva física no tiene)
    energia_ideal = df_ideal["Pmpp_ideal_w"].sum()
    energia_mppt = df_mppt["P_mppt_w"].sum()
    assert energia_mppt <= energia_ideal * 1.01, (
        f"Energía MPPT ({energia_mppt:.2f}) no puede superar la ideal "
        f"({energia_ideal:.2f}) más un 1% de margen numérico"
    )
    print(f"  ✓ potencia_mppt.csv coherente con potencia_ideal.csv "
          f"({len(df_mppt)} filas, energía MPPT ≤ energía ideal)")


# =====================================================================
# ETAPA 3: FASE 4 — INTERFAZ DE ESTADO ACTUAL
# =====================================================================
def test_fase4_interfaz_estado_actual():
    print("\n[Etapa 3] Fase 4 (Paso 15): interfaz de estado actual")

    from interfaz_estado_actual import obtener_estado_actual, _cargar_serie_mppt, RUTA_SERIE_MPPT

    df = _cargar_serie_mppt(str(RUTA_SERIE_MPPT))
    ts_prueba = df.index[len(df) // 2]  # un instante a mitad de la serie

    estado = obtener_estado_actual(ts_prueba)

    claves_esperadas = {"timestamp", "potencia_dc", "voltaje_dc", "corriente_dc",
                         "temperatura_panel", "irradiancia"}
    assert set(estado.keys()) == claves_esperadas, (
        f"El esquema del Paso 14 no coincide: {estado.keys()} vs {claves_esperadas}"
    )

    # Coherencia física básica: potencia = voltaje * corriente
    p_calculada = estado["voltaje_dc"] * estado["corriente_dc"]
    assert abs(p_calculada - estado["potencia_dc"]) < 0.01, (
        f"Inconsistencia potencia/voltaje/corriente en obtener_estado_actual: "
        f"{p_calculada} vs {estado['potencia_dc']}"
    )

    print(f"  ✓ obtener_estado_actual() devuelve el esquema correcto y "
          f"físicamente coherente: {estado}")


# =====================================================================
# MAIN
# =====================================================================
def ejecutar_todas_las_pruebas():
    print("=" * 70)
    print("PASO 16 (Fase 5): PRUEBA DE INTEGRACIÓN END-TO-END DEL PIPELINE")
    print("Fase 1 → Fase 2 → Fase 3 → Fase 4")
    print("=" * 70)

    test_precondicion_dataset_ambiental()
    test_fase2_validacion_y_aplicacion()
    test_fase3_simulacion_mppt()
    test_fase4_interfaz_estado_actual()

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETO EJECUTADO SIN ERRORES — INTEGRACIÓN OK")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()