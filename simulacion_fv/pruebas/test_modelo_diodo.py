"""
test_modelo_diodo.py
================================================================
Paso 16: Pruebas unitarias del modelo (casos límite).

Complementa las pruebas ya existentes dentro de cada módulo
(`modelo_diodo_unico.py`, `curva_caracteristica.py`,
`mppt_perturbar_observar.py`, `interfaz_estado_actual.py` ya
incluyen sus propias pruebas ejecutables con `python archivo.py`).
Este archivo se enfoca específicamente en los tres casos límite que
pide la guía metodológica:

    1. Irradiancia = 0 (de noche) → potencia debe ser 0.
    2. Temperatura muy alta → el modelo debe seguir siendo
       numéricamente estable (no debe lanzar excepciones ni devolver
       NaN/infinito, y el comportamiento físico debe degradarse de
       forma razonable, no arbitraria).
    3. Parámetros del panel fuera de rango físico → debe fallar de
       forma controlada (ValueError explícito desde
       ParametrosModulo.__post_init__, no un error numérico oscuro
       más adelante en el solver).

Estilo: se sigue el mismo patrón de "función ejecutable con asserts"
que ya usa el resto del proyecto (no se introduce pytest como
dependencia nueva), para poder correr con:

    python simulacion_fv/pruebas/test_modelo_diodo.py
================================================================
"""

import sys
import math
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planta"))
from modelo_diodo_unico import (   # noqa: E402
    ParametrosModulo,
    calcular_corriente,
    calcular_curva_iv,
    calcular_voc_ajustado,
)
from curva_caracteristica import resumen_punto_operativo  # noqa: E402


def _panel_referencia() -> ParametrosModulo:
    """Panel KC200GT calibrado (mismos valores que parametros_panel.yaml
    tras la calibración del Paso 9), usado como panel de referencia en
    estas pruebas para no depender de leer el archivo YAML."""
    return ParametrosModulo(
        Voc=32.9, Isc=8.21, Vmpp=26.3, Impp=7.61, Ns=72,
        alpha_Isc=0.0026, beta_Voc=-0.126,
        Rs=0.133619, Rsh=1038.4261, n=1.121061,
    )


# =====================================================================
# CASO 1: IRRADIANCIA = 0 (DE NOCHE)
# =====================================================================
def test_irradiancia_cero():
    print("\n[Caso 1] Irradiancia = 0 (de noche) → potencia debe ser 0")
    params = _panel_referencia()

    # 1a. Corriente en G=0 debe ser 0 para CUALQUIER voltaje válido
    for V in [0.0, 5.0, 15.0, params.Voc / 2, params.Voc - 0.01]:
        I = calcular_corriente(V, G=0.0, T_celsius=25.0, params=params)
        assert I == 0.0, f"Se esperaba I=0 en G=0, V={V}, se obtuvo {I}"
    print("  ✓ Corriente = 0 en G=0 para todo el rango de voltaje")

    # 1b. La curva I-V completa en G=0 debe ser degenerada (todo cero)
    voltajes, corrientes = calcular_curva_iv(G=0.0, T_celsius=25.0, params=params)
    assert np.all(corrientes == 0.0), "La curva en G=0 debería ser toda ceros"
    print("  ✓ Curva I-V completa en G=0 es toda ceros")

    # 1c. El resumen operativo (Pmpp) también debe ser 0
    resumen = resumen_punto_operativo(0.0, 25.0, params)
    assert resumen.Pmpp == 0.0, f"Pmpp debería ser 0 en G=0, se obtuvo {resumen.Pmpp}"
    assert resumen.Vmpp == 0.0 and resumen.Impp == 0.0
    print(f"  ✓ resumen_punto_operativo: Pmpp={resumen.Pmpp} W, Vmpp={resumen.Vmpp} V, "
          f"Impp={resumen.Impp} A")

    # 1d. Irradiancia negativa (dato corrupto/sensor con ruido): debe
    # tratarse igual que G=0, nunca generar corriente negativa/NaN.
    I_negativo = calcular_corriente(10.0, G=-5.0, T_celsius=25.0, params=params)
    assert I_negativo == 0.0, f"G negativa debería tratarse como G=0, se obtuvo {I_negativo}"
    print("  ✓ Irradiancia negativa (dato corrupto) se trata como G=0, sin errores")


# =====================================================================
# CASO 2: TEMPERATURA MUY ALTA (ESTABILIDAD NUMÉRICA)
# =====================================================================
def test_temperatura_alta():
    print("\n[Caso 2] Temperatura muy alta → estabilidad numérica")
    print("  Nota: por encima de ~65-70°C (fuera del rango realista de Bogotá,")
    print("  15-45°C aprox.), la corriente de saturación I0(T) crece de forma")
    print("  exponencial y el solver puede no converger en algunos puntos del")
    print("  barrido cerca de V=0. Esos puntos se resuelven a I=0 (fallback ya")
    print("  documentado en modelo_diodo_unico.py) y no impiden que Vmpp/Pmpp")
    print("  sigan siendo finitos y monótonamente decrecientes, que es lo que")
    print("  esta prueba verifica. No se contempló recalibrar el modelo para")
    print("  85-120°C por ser un rango fuera del alcance de esta tesis.")
    params = _panel_referencia()

    # Rango de temperaturas: desde condiciones normales hasta extremas
    # (85°C es un límite térmico típico de datasheet; 120°C es un
    # escenario de estrés fuera de operación normal, usado aquí solo
    # para verificar que el modelo no colapsa numéricamente).
    temperaturas = [25.0, 45.0, 65.0, 85.0, 120.0]

    resultados = []
    for T in temperaturas:
        # A temperaturas muy por encima del rango realista de operación
        # (>65-70°C), la corriente de saturación I0(T) crece de forma
        # exponencial y el solver de Brent puede no converger cerca de
        # V=0 en algunos puntos del barrido (ver limitación documentada
        # más abajo). Se capturan esas advertencias para no saturar la
        # consola; lo que importa para esta prueba es que el resultado
        # final (Vmpp, Impp, Pmpp) siga siendo finito y físicamente
        # coherente, lo cual SÍ se verifica explícitamente a continuación.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resumen = resumen_punto_operativo(1000.0, T, params)
        n_warnings = len(w)

        # No debe haber NaN ni infinitos en ningún resultado
        for campo, valor in [("Vmpp", resumen.Vmpp), ("Impp", resumen.Impp),
                              ("Pmpp", resumen.Pmpp), ("Voc", resumen.Voc)]:
            assert math.isfinite(valor), f"T={T}°C: {campo}={valor} no es finito"

        # Los valores deben seguir siendo físicamente plausibles
        assert resumen.Voc > 0.0, f"T={T}°C: Voc debería seguir siendo > 0"
        assert resumen.Pmpp >= 0.0, f"T={T}°C: Pmpp no puede ser negativo"
        assert resumen.Pmpp < 250.0, f"T={T}°C: Pmpp={resumen.Pmpp} supera lo físicamente esperable"

        resultados.append((T, resumen.Voc, resumen.Pmpp))
        aviso = f" ({n_warnings} advertencias del solver, ver limitación)" if n_warnings else ""
        print(f"  T={T:>6.1f}°C → Voc={resumen.Voc:6.3f} V, Pmpp={resumen.Pmpp:7.3f} W "
              f"(finito: {math.isfinite(resumen.Pmpp)}){aviso}")

    # Verificación de sentido físico: a más temperatura, el Voc debe
    # ser monótonamente decreciente (coeficiente beta_Voc negativo)
    voc_valores = [r[1] for r in resultados]
    assert all(voc_valores[i] > voc_valores[i + 1] for i in range(len(voc_valores) - 1)), (
        "Voc debería decrecer monótonamente con la temperatura"
    )
    print("  ✓ Voc decrece monótonamente con la temperatura (85°C y 120°C incluidos)")

    # Y la potencia también debería decrecer con la temperatura en STC
    # (a mayor T, mayor pérdida térmica, aunque Isc suba levemente)
    pmpp_valores = [r[2] for r in resultados]
    assert all(pmpp_valores[i] > pmpp_valores[i + 1] for i in range(len(pmpp_valores) - 1)), (
        "Pmpp debería decrecer monótonamente con la temperatura en STC"
    )
    print("  ✓ Pmpp decrece monótonamente con la temperatura (coherente con beta_Voc < 0)")


# =====================================================================
# CASO 3: PARÁMETROS FUERA DE RANGO FÍSICO → FALLO CONTROLADO
# =====================================================================
def test_parametros_fuera_de_rango():
    print("\n[Caso 3] Parámetros fuera de rango físico → debe fallar de forma controlada")

    casos_invalidos = [
        ("Rsh = 0 (división por cero en el modelo)", dict(Rsh=0.0)),
        ("Rsh negativa", dict(Rsh=-100.0)),
        ("Rs negativa", dict(Rs=-0.1)),
        ("n = 0 (factor de idealidad nulo)", dict(n=0.0)),
        ("n negativo", dict(n=-1.2)),
        ("Voc = 0", dict(Voc=0.0)),
        ("Isc negativa", dict(Isc=-8.21)),
        ("Ns = 0 (sin celdas)", dict(Ns=0)),
        ("Vmpp > Voc (físicamente imposible)", dict(Vmpp=50.0)),
        ("Impp > Isc (físicamente imposible)", dict(Impp=20.0)),
    ]

    base = dict(Voc=32.9, Isc=8.21, Vmpp=26.3, Impp=7.61, Ns=72,
                alpha_Isc=0.0026, beta_Voc=-0.126,
                Rs=0.133619, Rsh=1038.4261, n=1.121061)

    for descripcion, override in casos_invalidos:
        kwargs = {**base, **override}
        try:
            ParametrosModulo(**kwargs)
            raise AssertionError(
                f"Se esperaba ValueError para el caso '{descripcion}', pero no se lanzó ninguna excepción"
            )
        except ValueError as e:
            print(f"  ✓ {descripcion} → ValueError controlado: {str(e).splitlines()[0]}")

    # Caso adicional: parámetros válidos NO deben lanzar excepción
    ParametrosModulo(**base)
    print("  ✓ Parámetros físicamente válidos NO lanzan excepción (caso de control)")


# =====================================================================
# MAIN
# =====================================================================
def ejecutar_todas_las_pruebas():
    print("=" * 70)
    print("PASO 16: PRUEBAS UNITARIAS DE CASOS LÍMITE DEL MODELO")
    print("=" * 70)

    test_irradiancia_cero()
    test_temperatura_alta()
    test_parametros_fuera_de_rango()

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS DE CASOS LÍMITE PASARON CORRECTAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()