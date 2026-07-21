"""
mppt_perturbar_observar.py
================================================================
Paso 11: Implementar el MPPT como función de estado.

A diferencia de calcular_curva_iv / resumen_punto_operativo (Paso 8),
que encuentran el MPP "a fuerza bruta" barriendo todo el rango de
voltaje, este módulo simula cómo un inversor real converge SIN conocer
la curva completa: en cada ciclo, el inversor solo conoce el voltaje y
la potencia del ciclo anterior, y decide en qué dirección mover el
voltaje de operación para el siguiente ciclo (algoritmo Perturbar y
Observar / P&O).

El algoritmo es intencionalmente una función de estado explícito
(EstadoMPPT en, EstadoMPPT out), no un bucle con variables globales:
esto permite probarlo de forma aislada (Paso 16) y reutilizarlo tanto
en la simulación completa (Paso 12) como más adelante en un lazo de
control real (envuelto por Modbus/MQTT), sin cambiar su lógica interna.

Lógica de Perturbar y Observar:
    1. Se mide la potencia en el voltaje de operación actual.
    2. Se compara contra la potencia del ciclo anterior.
    3. Si la potencia aumentó, se sigue perturbando en la misma
       dirección (se está "subiendo la colina" de la curva P-V).
    4. Si la potencia disminuyó, se invierte la dirección (se pasó
       el máximo o las condiciones ambientales cambiaron).
    5. El voltaje de operación se actualiza en ±paso_V para el
       siguiente ciclo.

El "paso" de perturbación (paso_V) es un parámetro configurable:
    - Paso grande  → converge más rápido ante cambios bruscos de
      irradiancia, pero oscila más alrededor del MPP en estado
      estacionario (mayor "ripple", menor eficiencia de seguimiento).
    - Paso pequeño → oscila menos y sigue el MPP con más precisión en
      estado estacionario, pero reacciona más lento ante cambios
      bruscos (ej. una nube tapando el sol), quedándose temporalmente
      lejos del MPP real mientras converge.
Este compromiso (velocidad vs. precisión) se compara empíricamente en
el Paso 13 (docs/06_experimentacion/eficiencia_mppt.md).

Uso:
    from mppt_perturbar_observar import EstadoMPPT, paso_mppt

    estado = EstadoMPPT(V_operacion=20.0, P_anterior=0.0, direccion=1, paso_V=0.5)
    estado = paso_mppt(estado, G=800.0, T=30.0, params=parametros_panel)
================================================================
"""

import sys
from pathlib import Path
from dataclasses import dataclass, replace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planta"))
from modelo_diodo_unico import (   # noqa: E402
    ParametrosModulo, calcular_corriente, calcular_voc_ajustado, calcular_voc_estimado_gt,
)


# =====================================================================
# ESTADO DEL MPPT
# =====================================================================
@dataclass(frozen=True)
class EstadoMPPT:
    """
    Estado completo del algoritmo P&O entre un ciclo y el siguiente.

    Atributos:
        V_operacion: voltaje de operación decidido para ESTE ciclo (V).
        P_anterior: potencia medida en el ciclo ANTERIOR (W). Se usa
            como referencia de comparación en este ciclo.
        direccion: +1 o -1, sentido de la última perturbación aplicada.
        paso_V: magnitud del paso de perturbación (V), configurable.
    """
    V_operacion: float
    P_anterior: float
    direccion: int
    paso_V: float


def estado_inicial(params: ParametrosModulo, paso_V: float = 0.5,
                    fraccion_voc_arranque: float = 0.6) -> EstadoMPPT:
    """
    Estado de arranque del inversor: sin medición previa (P_anterior=0)
    y un voltaje de operación inicial típico de arranque, una fracción
    del Voc nominal en STC (heurística común en inversores reales para
    no arrancar ni en cortocircuito ni en circuito abierto).
    """
    V_inicial = fraccion_voc_arranque * calcular_voc_ajustado(25.0, params)
    return EstadoMPPT(V_operacion=V_inicial, P_anterior=0.0, direccion=1, paso_V=paso_V)


# =====================================================================
# UN CICLO DEL ALGORITMO P&O (Paso 11)
# =====================================================================
def paso_mppt(estado: EstadoMPPT, G: float, T: float, params: ParametrosModulo) -> tuple:
    """
    Ejecuta un ciclo del algoritmo Perturbar y Observar.

    Función de estado pura: no lee archivos ni usa variables globales.
    Recibe el estado del ciclo anterior y las condiciones ambientales
    ACTUALES, y devuelve el nuevo estado (con el voltaje que se
    aplicará en el siguiente ciclo) junto con la potencia medida en
    ESTE ciclo (con el voltaje decidido en el ciclo anterior).

    Argumentos:
        estado: EstadoMPPT del ciclo anterior.
        G: irradiancia actual (W/m²).
        T: temperatura actual (°C).
        params: parámetros del panel (calibrados, Paso 9).

    Retorna:
        (nuevo_estado, P_medida): nuevo_estado.V_operacion es el
        voltaje a aplicar en el PRÓXIMO ciclo; P_medida es la potencia
        que efectivamente entregó el panel EN ESTE ciclo, con el
        voltaje decidido en el ciclo anterior (estado.V_operacion).
    """
    # 1. Medir la potencia en el voltaje de operación actual
    I_medida = calcular_corriente(estado.V_operacion, G, T, params)
    P_medida = estado.V_operacion * I_medida

    # 2. Comparar contra el ciclo anterior y decidir la dirección
    delta_P = P_medida - estado.P_anterior

    if delta_P > 0:
        # La potencia subió: se sigue perturbando en la misma dirección
        nueva_direccion = estado.direccion
    elif delta_P < 0:
        # La potencia bajó: se invierte la dirección (se pasó el MPP
        # o cambiaron las condiciones ambientales)
        nueva_direccion = -estado.direccion
    else:
        # Sin cambio (delta_P == 0): se mantiene la dirección actual
        nueva_direccion = estado.direccion

    # 3. Calcular el nuevo voltaje de operación, acotado a un rango
    #    físicamente válido [0, Voc(G,T)] para evitar que el algoritmo
    #    "se salga" de la curva por acumulación de pasos. Se usa el Voc
    #    dependiente de G (no solo de T): a irradiancias bajas/medias
    #    el Voc real cae de forma importante respecto al valor STC
    #    (ver calcular_voc_estimado_gt en modelo_diodo_unico.py).
    Voc_actual = calcular_voc_estimado_gt(G, T, params)
    if Voc_actual <= 0.0:
        Voc_actual = calcular_voc_ajustado(T, params)  # G=0: solo referencia, I será 0 igual
    nuevo_V = estado.V_operacion + nueva_direccion * estado.paso_V
    nuevo_V = max(0.0, min(nuevo_V, Voc_actual))

    nuevo_estado = replace(
        estado,
        V_operacion=nuevo_V,
        P_anterior=P_medida,
        direccion=nueva_direccion,
    )

    return nuevo_estado, P_medida


# =====================================================================
# PRUEBAS UNITARIAS BÁSICAS (complementan Paso 16)
# =====================================================================
def ejecutar_pruebas_unitarias():
    print("=" * 70)
    print("PRUEBAS UNITARIAS DEL MPPT PERTURBAR Y OBSERVAR (Paso 11)")
    print("=" * 70)

    params = ParametrosModulo(
        Voc=32.9, Isc=8.21, Vmpp=26.3, Impp=7.61, Ns=72,
        alpha_Isc=0.0026, beta_Voc=-0.126,
        Rs=0.133619, Rsh=1038.4261, n=1.121061,
    )

    # Prueba 1: en G=0 (noche), la potencia medida debe ser 0
    print("\n[Prueba 1] G=0 (noche) → potencia medida debe ser 0")
    estado = estado_inicial(params, paso_V=0.5)
    nuevo_estado, P = paso_mppt(estado, G=0.0, T=20.0, params=params)
    assert P == 0.0, f"Se esperaba P=0, se obtuvo {P}"
    print(f"  ✓ P = {P} W")

    # Prueba 2: partiendo de V muy bajo, con delta_P>0 al inicio, debe
    # seguir subiendo el voltaje en la misma dirección
    print("\n[Prueba 2] Al inicio (P_anterior=0), la primera potencia medida")
    print("            es > 0 en STC → debe mantener dirección +1")
    estado = estado_inicial(params, paso_V=0.5)
    V0 = estado.V_operacion
    nuevo_estado, P = paso_mppt(estado, G=1000.0, T=25.0, params=params)
    assert nuevo_estado.direccion == 1, "La dirección debería mantenerse en +1"
    assert nuevo_estado.V_operacion == V0 + 0.5, "El voltaje debió incrementarse en paso_V"
    print(f"  ✓ V: {V0:.3f} V → {nuevo_estado.V_operacion:.3f} V, dirección = "
          f"{nuevo_estado.direccion}")

    # Prueba 3: el algoritmo debe converger cerca del Vmpp real cuando
    # las condiciones son constantes durante muchos ciclos
    print("\n[Prueba 3] Convergencia bajo condiciones constantes (STC, 200 ciclos)")
    estado = estado_inicial(params, paso_V=0.1)
    for _ in range(200):
        estado, P = paso_mppt(estado, G=1000.0, T=25.0, params=params)
    print(f"  V final = {estado.V_operacion:.3f} V (Vmpp datasheet = {params.Vmpp} V)")
    assert abs(estado.V_operacion - params.Vmpp) < 1.0, (
        f"El MPPT no convergió cerca de Vmpp: {estado.V_operacion} vs {params.Vmpp}"
    )
    print(f"  ✓ Convergió a {abs(estado.V_operacion - params.Vmpp):.3f} V del Vmpp real")

    # Prueba 4: el voltaje nunca debe salir del rango físico [0, Voc]
    print("\n[Prueba 4] El voltaje de operación nunca sale de [0, Voc]")
    estado = EstadoMPPT(V_operacion=0.0, P_anterior=0.0, direccion=-1, paso_V=5.0)
    for _ in range(20):
        estado, P = paso_mppt(estado, G=1000.0, T=25.0, params=params)
        assert 0.0 <= estado.V_operacion <= calcular_voc_ajustado(25.0, params) + 1e-9
    print(f"  ✓ V se mantuvo siempre en [0, {calcular_voc_ajustado(25.0, params):.2f}] V")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON CORRECTAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_pruebas_unitarias()