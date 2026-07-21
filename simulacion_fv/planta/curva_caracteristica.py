"""
generar_curva_iv_pv.py
================================================================
Paso 8: Generar la curva I-V y P-V completa para condiciones
dadas de irradiancia (G) y temperatura (T).

Este módulo consume el modelo de diodo único (Paso 7) y produce:
  - Curvas I-V y P-V completas (bajo demanda, para validación/tesis)
  - Resumen operativo por punto: Vmpp, Impp, Pmpp, Voc, Isc, FF
    (para uso masivo en el Paso 10)

DECISIONES DE DISEÑO (justificadas para la tesis):
  1. Rango de barrido: [0, Voc_ajustado(T)] con 200 puntos por defecto.
     Voc se recalcula para cada T (no se usa el Voc STC fijo).
  2. Refinamiento del MPP: interpolación parabólica de 3 puntos
     alrededor del máximo discreto. Mejora la precisión sin costo
     significativo y es defendible analíticamente.
  3. Sanity checks: se verifica monotonicidad de I(V) y unimodalidad
     de P(V). Fallos → warnings, no excepciones (para no romper
     el pipeline masivo del Paso 10).
  4. Fallos del solver: se fuerzan a I=0 y se registran en el
     resumen como "puntos_no_convergentes" para trazabilidad.

Uso:
    from generar_curva_iv_pv import generar_curva_iv_pv, resumen_punto_operativo
    
    # Curva completa (para figuras de tesis)
    curva = generar_curva_iv_pv(G=1000.0, T=25.0, params)
    
    # Solo resumen (para pipeline masivo)
    resumen = resumen_punto_operativo(G=1000.0, T=25.0, params)

Salida:
    - Funciones puras (sin I/O de archivos)
    - Figura de validación al ejecutar directamente
================================================================
"""

import warnings
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Optional

from modelo_diodo_unico import (
    ParametrosModulo,
    calcular_curva_iv,
    calcular_voc_ajustado,
    calcular_corriente_fotogenerada,
    calcular_corriente_saturacion,
    calcular_voltaje_termino,
    T_REF,
)

# =====================================================================
# CONFIGURACIÓN GLOBAL
# =====================================================================
N_PUNTOS_BARRIDO = 200          # Resolución del barrido de voltaje
REFINAR_MPP = True              # Interpolación parabólica alrededor del máximo
TOLERANCIA_MONOTONICIDAD = 1e-4 # A - Margen para ruido numérico en I(V)
AREA_MODULO_M2 = 1.65           # m² - Área típica de módulo ~300W (para η)


# =====================================================================
# SANITY CHECKS (Paso 8.5)
# =====================================================================

def verificar_monotonicidad_corriente(voltajes: np.ndarray, corrientes: np.ndarray) -> dict:
    """
    Verifica que la corriente decrezca de forma monótona con el voltaje.
    
    Permite pequeñas violaciones numéricas (≤ TOLERANCIA_MONOTONICIDAD)
    debidas a la tolerancia del solver de Brent.
    
    Retorna:
        dict con 'es_monotona', 'n_violaciones', 'max_violacion'
    """
    diff_I = np.diff(corrientes)
    violaciones = diff_I > TOLERANCIA_MONOTONICIDAD
    n_violaciones = int(violaciones.sum())
    max_violacion = float(diff_I[violaciones].max()) if n_violaciones > 0 else 0.0
    
    return {
        "es_monotona": n_violaciones == 0,
        "n_violaciones": n_violaciones,
        "max_violacion_A": max_violacion,
    }


def verificar_unimodalidad_potencia(voltajes: np.ndarray, potencias: np.ndarray) -> dict:
    """
    Verifica que la curva de potencia tenga un único pico (unimodal).
    
    Cuenta los cambios de signo en dP/dV: debe haber exactamente 1
    (de positivo a negativo).
    
    Retorna:
        dict con 'es_unimodal', 'n_picos_detectados'
    """
    diff_P = np.diff(potencias)
    # Cambios de signo: donde diff_P pasa de + a - o viceversa
    signos = np.sign(diff_P)
    # Ignorar ceros (mesetas)
    signos_no_cero = signos[signos != 0]
    if len(signos_no_cero) == 0:
        return {"es_unimodal": True, "n_picos_detectados": 0}
    
    cambios_signo = np.diff(signos_no_cero)
    n_picos = int((cambios_signo < 0).sum())  # Transiciones + → -
    
    return {
        "es_unimodal": n_picos <= 1,
        "n_picos_detectados": n_picos,
    }


def ejecutar_sanity_checks(voltajes: np.ndarray, corrientes: np.ndarray, 
                           potencias: np.ndarray) -> dict:
    """
    Ejecuta todos los sanity checks y retorna un resumen.
    Emite warnings si algo falla, pero no lanza excepciones.
    """
    check_I = verificar_monotonicidad_corriente(voltajes, corrientes)
    check_P = verificar_unimodalidad_potencia(voltajes, potencias)
    
    if not check_I["es_monotona"]:
        warnings.warn(
            f"Sanity check: I(V) no es estrictamente monótona. "
            f"Violaciones: {check_I['n_violaciones']}, "
            f"max: {check_I['max_violacion_A']:.2e} A. "
            f"Posible problema de convergencia del solver.",
            RuntimeWarning,
            stacklevel=2,
        )
    
    if not check_P["es_unimodal"]:
        warnings.warn(
            f"Sanity check: P(V) no es unimodal. Picos detectados: "
            f"{check_P['n_picos_detectados']}. "
            f"Revisar parámetros del modelo.",
            RuntimeWarning,
            stacklevel=2,
        )
    
    return {
        "monotonicidad_I": check_I,
        "unimodalidad_P": check_P,
        "curva_valida": check_I["es_monotona"] and check_P["es_unimodal"],
    }


# =====================================================================
# REFINAMIENTO DEL MPP POR PARÁBOLA (Paso 8.4)
# =====================================================================

def refinar_mpp_parabola(voltajes: np.ndarray, corrientes: np.ndarray, 
                         potencias: np.ndarray, idx_max: int) -> dict:
    """
    Refina la ubicación del MPP mediante interpolación parabólica
    de 3 puntos alrededor del máximo discreto.
    
    Dado que P(V) cerca del máximo es aproximadamente parabólica,
    ajustar una parábola a (V_{i-1}, P_{i-1}), (V_i, P_i), (V_{i+1}, P_{i+1})
    y calcular su vértice da una estimación más precisa que el máximo discreto.
    
    Retorna:
        dict con Vmpp, Impp, Pmpp refinados
    """
    n = len(voltajes)
    
    # Casos límite: máximo en los extremos → no se puede refinar
    if idx_max == 0 or idx_max == n - 1:
        return {
            "Vmpp": float(voltajes[idx_max]),
            "Impp": float(corrientes[idx_max]),
            "Pmpp": float(potencias[idx_max]),
            "refinado": False,
            "motivo": "máximo en extremo del barrido",
        }
    
    # Tres puntos alrededor del máximo
    V_m1, V_0, V_p1 = voltajes[idx_max - 1], voltajes[idx_max], voltajes[idx_max + 1]
    P_m1, P_0, P_p1 = potencias[idx_max - 1], potencias[idx_max], potencias[idx_max + 1]
    I_m1, I_0, I_p1 = corrientes[idx_max - 1], corrientes[idx_max], corrientes[idx_max + 1]
    
    # Ancho de paso (asumido uniforme)
    dV = V_0 - V_m1
    
    # Coeficientes de la parábola P(V) = a*V² + b*V + c
    # Usando diferencias finitas centradas:
    a = (P_m1 - 2 * P_0 + P_p1) / (2 * dV ** 2)
    
    if abs(a) < 1e-12:
        # Parábola degenerada (plana) → usar máximo discreto
        return {
            "Vmpp": float(V_0),
            "Impp": float(I_0),
            "Pmpp": float(P_0),
            "refinado": False,
            "motivo": "curvatura parabólica despreciable",
        }
    
    # Vértice de la parábola
    V_mpp_ref = - (P_p1 - P_m1) / (4 * a * dV) + V_0
    
    # Verificar que el vértice esté dentro del intervalo [V_{i-1}, V_{i+1}]
    if not (V_m1 <= V_mpp_ref <= V_p1):
        return {
            "Vmpp": float(V_0),
            "Impp": float(I_0),
            "Pmpp": float(P_0),
            "refinado": False,
            "motivo": f"vértice fuera de intervalo ({V_mpp_ref:.3f}V)",
        }
    
    # Interpolar I en V_mpp_ref por parábola también
    a_I = (I_m1 - 2 * I_0 + I_p1) / (2 * dV ** 2)
    b_I = (I_p1 - I_m1) / (2 * dV)
    I_mpp_ref = a_I * (V_mpp_ref - V_0) ** 2 + b_I * (V_mpp_ref - V_0) + I_0
    
    P_mpp_ref = V_mpp_ref * I_mpp_ref
    
    return {
        "Vmpp": float(V_mpp_ref),
        "Impp": float(I_mpp_ref),
        "Pmpp": float(P_mpp_ref),
        "refinado": True,
        "motivo": "interpolación parabólica de 3 puntos",
    }


# =====================================================================
# FUNCIÓN PRINCIPAL: CURVA COMPLETA (Paso 8.1 - 8.6)
# =====================================================================

@dataclass
class ResultadoCurvaIV:
    """Contenedor de resultados de la curva I-V/P-V completa."""
    # Arrays de la curva
    voltajes: np.ndarray
    corrientes: np.ndarray
    potencias: np.ndarray
    
    # Punto de máxima potencia
    Vmpp: float
    Impp: float
    Pmpp: float
    
    # Puntos característicos
    Voc: float
    Isc: float
    
    # Métricas derivadas
    FF: float           # Factor de llenado
    eta: float          # Eficiencia (requiere AREA_MODULO_M2)
    
    # Sanity checks
    curva_valida: bool
    detalles_checks: dict
    
    # Refinamiento
    mpp_refinado: bool
    metodo_mpp: str
    
    # Trazabilidad
    puntos_no_convergentes: int
    n_puntos_barrido: int
    G: float
    T: float


def generar_curva_iv_pv(
    G: float,
    T_celsius: float,
    params: ParametrosModulo,
    n_puntos: int = N_PUNTOS_BARRIDO,
    refinar_mpp: bool = REFINAR_MPP,
    area_modulo: float = AREA_MODULO_M2,
) -> ResultadoCurvaIV:
    """
    Genera la curva I-V y P-V completa para condiciones (G, T) dadas.
    
    PASO 8.1 - Rango de barrido:
        [0, Voc_ajustado(T)] con `n_puntos` puntos.
        Voc se recalcula para la temperatura actual (no se usa STC fijo).
    
    PASO 8.2 - Corriente en cada punto:
        Delega en `calcular_curva_iv()` del Paso 7, que ya maneja
        fallos del solver con warnings.
    
    PASO 8.3 - Curva de potencia:
        P = V × I. Se verifica que no haya potencias negativas espurias.
    
    PASO 8.4 - MPP:
        Máximo discreto + refinamiento parabólico opcional.
    
    PASO 8.5 - Sanity checks:
        Monotonicidad de I(V) y unimodalidad de P(V).
    
    Parámetros:
        G: irradiancia en W/m²
        T_celsius: temperatura en °C
        params: parámetros del módulo
        n_puntos: resolución del barrido (default: 200)
        refinar_mpp: aplicar interpolación parabólica (default: True)
        area_modulo: área del módulo en m² para calcular η (default: 1.65)
    
    Retorna:
        ResultadoCurvaIV con toda la información de la curva
    """
    
    # =================================================================
    # PASO 8.1: Rango de barrido con Voc dependiente de T
    # =================================================================
    Voc_ajustado = calcular_voc_ajustado(T_celsius, params)
    
    # Caso límite: G = 0 → curva trivial
    if G <= 0.0:
        return ResultadoCurvaIV(
            voltajes=np.array([0.0, Voc_ajustado]),
            corrientes=np.array([0.0, 0.0]),
            potencias=np.array([0.0, 0.0]),
            Vmpp=0.0, Impp=0.0, Pmpp=0.0,
            Voc=Voc_ajustado, Isc=0.0,
            FF=0.0, eta=0.0,
            curva_valida=True,
            detalles_checks={"motivo": "G=0, curva trivial"},
            mpp_refinado=False,
            metodo_mpp="trivial_G_cero",
            puntos_no_convergentes=0,
            n_puntos_barrido=2,
            G=G, T=T_celsius,
        )
    
    voltajes = np.linspace(0.0, Voc_ajustado, n_puntos)
    
    # =================================================================
    # PASO 8.2: Resolver corriente en cada punto
    # =================================================================
    voltajes, corrientes = calcular_curva_iv(G, T_celsius, params, n_puntos=n_puntos)
    
    # Contar puntos donde la corriente es 0 por fallo del solver
    # (excluyendo el punto V=Voc donde I=0 es físico)
    puntos_no_convergentes = 0
    for i, V in enumerate(voltajes):
        if V < Voc_ajustado * 0.99 and corrientes[i] == 0.0:
            # Si V está lejos de Voc y la corriente es 0, probablemente
            # el solver falló (no es el caso límite V=0 ni V=Voc)
            puntos_no_convergentes += 1
    
    # =================================================================
    # PASO 8.3: Curva de potencia
    # =================================================================
    potencias = voltajes * corrientes
    
    # Verificar potencias negativas espurias
    potencias_negativas = potencias < 0
    if potencias_negativas.any():
        n_neg = potencias_negativas.sum()
        warnings.warn(
            f"Se detectaron {n_neg} valores de potencia negativa espuria. "
            f"Forzados a 0.",
            RuntimeWarning,
            stacklevel=2,
        )
        potencias[potencias_negativas] = 0.0
    
    # =================================================================
    # PASO 8.4: Localizar MPP
    # =================================================================
    idx_max_discreto = int(np.argmax(potencias))
    Vmpp_discreto = float(voltajes[idx_max_discreto])
    Impp_discreto = float(corrientes[idx_max_discreto])
    Pmpp_discreto = float(potencias[idx_max_discreto])
    
    if refinar_mpp:
        refinamiento = refinar_mpp_parabola(
            voltajes, corrientes, potencias, idx_max_discreto
        )
        Vmpp = refinamiento["Vmpp"]
        Impp = refinamiento["Impp"]
        Pmpp = refinamiento["Pmpp"]
        mpp_refinado = refinamiento["refinado"]
        metodo_mpp = refinamiento["motivo"]
    else:
        Vmpp = Vmpp_discreto
        Impp = Impp_discreto
        Pmpp = Pmpp_discreto
        mpp_refinado = False
        metodo_mpp = "máximo discreto sin refinar"
    
    # =================================================================
    # Puntos característicos
    # =================================================================
    Voc = Voc_ajustado
    Isc = float(corrientes[0])  # Corriente en V=0
    
    # =================================================================
    # Métricas derivadas
    # =================================================================
    # Factor de llenado: FF = (Vmpp × Impp) / (Voc × Isc)
    if Voc > 0 and Isc > 0:
        FF = (Vmpp * Impp) / (Voc * Isc)
    else:
        FF = 0.0
    
    # Eficiencia: η = Pmpp / (G × A)
    if G > 0 and area_modulo > 0:
        eta = Pmpp / (G * area_modulo)
    else:
        eta = 0.0
    
    # =================================================================
    # PASO 8.5: Sanity checks
    # =================================================================
    detalles_checks = ejecutar_sanity_checks(voltajes, corrientes, potencias)
    
    return ResultadoCurvaIV(
        voltajes=voltajes,
        corrientes=corrientes,
        potencias=potencias,
        Vmpp=Vmpp,
        Impp=Impp,
        Pmpp=Pmpp,
        Voc=Voc,
        Isc=Isc,
        FF=FF,
        eta=eta,
        curva_valida=detalles_checks["curva_valida"],
        detalles_checks=detalles_checks,
        mpp_refinado=mpp_refinado,
        metodo_mpp=metodo_mpp,
        puntos_no_convergentes=puntos_no_convergentes,
        n_puntos_barrido=n_puntos,
        G=G,
        T=T_celsius,
    )


# =====================================================================
# FUNCIÓN RESUMEN: PARA USO MASIVO (Paso 8.6)
# =====================================================================

@dataclass
class ResumenOperativo:
    """Resumen de un punto operativo (G, T) para uso masivo."""
    G: float
    T: float
    Vmpp: float
    Impp: float
    Pmpp: float
    Voc: float
    Isc: float
    FF: float
    eta: float
    curva_valida: bool
    puntos_no_convergentes: int


def resumen_punto_operativo(
    G: float,
    T_celsius: float,
    params: ParametrosModulo,
    n_puntos: int = N_PUNTOS_BARRIDO,
    refinar_mpp: bool = REFINAR_MPP,
    area_modulo: float = AREA_MODULO_M2,
) -> ResumenOperativo:
    """
    Genera solo el resumen operativo de un punto (G, T).
    
    Diseñado para el Paso 10 (miles de instantes): evita almacenar
    las curvas completas y retorna únicamente las métricas clave.
    
    La curva completa puede regenerarse bajo demanda llamando a
    `generar_curva_iv_pv()` con los mismos parámetros.
    
    Retorna:
        ResumenOperativo con Vmpp, Impp, Pmpp, Voc, Isc, FF, η
    """
    curva = generar_curva_iv_pv(
        G, T_celsius, params,
        n_puntos=n_puntos,
        refinar_mpp=refinar_mpp,
        area_modulo=area_modulo,
    )
    
    return ResumenOperativo(
        G=curva.G,
        T=curva.T,
        Vmpp=curva.Vmpp,
        Impp=curva.Impp,
        Pmpp=curva.Pmpp,
        Voc=curva.Voc,
        Isc=curva.Isc,
        FF=curva.FF,
        eta=curva.eta,
        curva_valida=curva.curva_valida,
        puntos_no_convergentes=curva.puntos_no_convergentes,
    )


# =====================================================================
# VISUALIZACIÓN PARA VALIDACIÓN (Paso 8.6 - figuras de tesis)
# =====================================================================

def graficar_curva_iv_pv(curva: ResultadoCurvaIV, ruta_guardado: Optional[str] = None):
    """
    Genera una figura de validación con las curvas I-V y P-V superpuestas,
    marcando el MPP y los puntos característicos (Voc, Isc).
    
    Útil para las figuras del Paso 9 y de la tesis.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # --- Curva I-V ---
    ax1.plot(curva.voltajes, curva.corrientes, "b-", linewidth=2, label="I(V)")
    ax1.plot(curva.Vmpp, curva.Impp, "ro", markersize=10, label=f"MPP ({curva.Vmpp:.2f}V, {curva.Impp:.2f}A)")
    ax1.plot(curva.Voc, 0, "gs", markersize=10, label=f"Voc={curva.Voc:.2f}V")
    ax1.plot(0, curva.Isc, "m^", markersize=10, label=f"Isc={curva.Isc:.2f}A")
    ax1.set_xlabel("Voltaje (V)")
    ax1.set_ylabel("Corriente (A)")
    ax1.set_title(f"Curva I-V | G={curva.G} W/m², T={curva.T}°C")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # --- Curva P-V ---
    ax2.plot(curva.voltajes, curva.potencias, "g-", linewidth=2, label="P(V)")
    ax2.plot(curva.Vmpp, curva.Pmpp, "ro", markersize=10, label=f"Pmpp={curva.Pmpp:.2f}W")
    ax2.axhline(y=curva.Pmpp, color="r", linestyle="--", alpha=0.5)
    ax2.axvline(x=curva.Vmpp, color="r", linestyle="--", alpha=0.5)
    ax2.set_xlabel("Voltaje (V)")
    ax2.set_ylabel("Potencia (W)")
    ax2.set_title(f"Curva P-V | FF={curva.FF:.3f}, η={curva.eta*100:.2f}%")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if ruta_guardado:
        plt.savefig(ruta_guardado, dpi=300, bbox_inches="tight")
        print(f"Figura guardada: {ruta_guardado}")
    else:
        plt.show()
    
    plt.close()


# =====================================================================
# PRUEBAS BÁSICAS
# =====================================================================

def ejecutar_pruebas():
    """Validación rápida del módulo."""
    print("\n" + "=" * 70)
    print("PRUEBAS DEL PASO 8: GENERAR CURVA I-V / P-V")
    print("=" * 70)
    
    params = ParametrosModulo()
    
    # =================================================================
    # PRUEBA 1: Curva en STC (G=1000, T=25)
    # =================================================================
    print("\n[Prueba 1] Curva en STC (G=1000 W/m², T=25°C)")
    curva = generar_curva_iv_pv(1000.0, 25.0, params)
    
    print(f"  Voc = {curva.Voc:.2f} V (esperado: ~37.5 V)")
    print(f"  Isc = {curva.Isc:.4f} A (esperado: ~8.5 A)")
    print(f"  Vmpp = {curva.Vmpp:.2f} V")
    print(f"  Impp = {curva.Impp:.4f} A")
    print(f"  Pmpp = {curva.Pmpp:.2f} W")
    print(f"  FF = {curva.FF:.4f}")
    print(f"  η = {curva.eta*100:.2f}%")
    print(f"  MPP refinado: {curva.mpp_refinado} ({curva.metodo_mpp})")
    print(f"  Curva válida: {curva.curva_valida}")
    print(f"  Puntos no convergentes: {curva.puntos_no_convergentes}")
    
    assert curva.Voc > 35 and curva.Voc < 40, f"Voc fuera de rango: {curva.Voc}"
    assert curva.Isc > 8.0 and curva.Isc < 9.0, f"Isc fuera de rango: {curva.Isc}"
    assert curva.Pmpp > 200, f"Pmpp demasiado bajo: {curva.Pmpp}"
    assert curva.curva_valida, "Sanity checks fallaron"
    print("  ✓ Prueba 1 OK")
    
    # =================================================================
    # PRUEBA 2: Curva en NOCT aproximado (G=800, T=45)
    # =================================================================
    print("\n[Prueba 2] Curva en NOCT aproximado (G=800 W/m², T=45°C)")
    curva_noct = generar_curva_iv_pv(800.0, 45.0, params)
    
    print(f"  Voc = {curva_noct.Voc:.2f} V (debe ser < Voc STC)")
    print(f"  Pmpp = {curva_noct.Pmpp:.2f} W (debe ser < Pmpp STC)")
    
    assert curva_noct.Voc < curva.Voc, "Voc NOCT debe ser menor que Voc STC"
    assert curva_noct.Pmpp < curva.Pmpp, "Pmpp NOCT debe ser menor que Pmpp STC"
    print("  ✓ Prueba 2 OK")
    
    # =================================================================
    # PRUEBA 3: G = 0 (noche)
    # =================================================================
    print("\n[Prueba 3] Curva en noche (G=0)")
    curva_noche = generar_curva_iv_pv(0.0, 25.0, params)
    
    assert curva_noche.Pmpp == 0.0, "Pmpp debe ser 0 en la noche"
    assert curva_noche.Isc == 0.0, "Isc debe ser 0 en la noche"
    print(f"  Pmpp = {curva_noche.Pmpp} W")
    print("  ✓ Prueba 3 OK")
    
    # =================================================================
    # PRUEBA 4: Resumen operativo
    # =================================================================
    print("\n[Prueba 4] Resumen operativo")
    resumen = resumen_punto_operativo(1000.0, 25.0, params)
    
    print(f"  Vmpp={resumen.Vmpp:.2f}V, Impp={resumen.Impp:.4f}A, Pmpp={resumen.Pmpp:.2f}W")
    assert abs(resumen.Vmpp - curva.Vmpp) < 1e-6, "Resumen debe coincidir con curva completa"
    print("  ✓ Prueba 4 OK")
    
    # =================================================================
    # PRUEBA 5: Sanity check - monotonicidad
    # =================================================================
    print("\n[Prueba 5] Sanity check - monotonicidad de I(V)")
    diff_I = np.diff(curva.corrientes)
    n_violaciones = (diff_I > TOLERANCIA_MONOTONICIDAD).sum()
    print(f"  Violaciones de monotonicidad: {n_violaciones}")
    assert n_violaciones == 0, f"Curva no monótona: {n_violaciones} violaciones"
    print("  ✓ Prueba 5 OK")
    
    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("=" * 70)


# =====================================================================
# EJEMPLO DE USO CON FIGURA DE VALIDACIÓN
# =====================================================================

def ejemplo_con_figura():
    """Genera una figura de validación para la tesis."""
    print("\n" + "=" * 70)
    print("EJEMPLO: Generando figura de validación I-V / P-V")
    print("=" * 70)
    
    params = ParametrosModulo()
    
    # Tres condiciones representativas
    condiciones = [
        (1000.0, 25.0, "STC (1000 W/m², 25°C)"),
        (800.0, 45.0, "NOCT aprox. (800 W/m², 45°C)"),
        (500.0, 35.0, "Parcial (500 W/m², 35°C)"),
    ]
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    
    for idx, (G, T, titulo) in enumerate(condiciones):
        curva = generar_curva_iv_pv(G, T, params)
        
        # I-V
        ax_iv = axes[0, idx]
        ax_iv.plot(curva.voltajes, curva.corrientes, "b-", linewidth=2)
        ax_iv.plot(curva.Vmpp, curva.Impp, "ro", markersize=8)
        ax_iv.set_title(f"I-V: {titulo}")
        ax_iv.set_xlabel("V (V)")
        ax_iv.set_ylabel("I (A)")
        ax_iv.grid(True, alpha=0.3)
        
        # P-V
        ax_pv = axes[1, idx]
        ax_pv.plot(curva.voltajes, curva.potencias, "g-", linewidth=2)
        ax_pv.plot(curva.Vmpp, curva.Pmpp, "ro", markersize=8)
        ax_pv.set_title(f"P-V: Pmpp={curva.Pmpp:.1f}W, FF={curva.FF:.3f}")
        ax_pv.set_xlabel("V (V)")
        ax_pv.set_ylabel("P (W)")
        ax_pv.grid(True, alpha=0.3)
        
        print(f"  {titulo}: Vmpp={curva.Vmpp:.2f}V, Impp={curva.Impp:.3f}A, "
              f"Pmpp={curva.Pmpp:.2f}W, FF={curva.FF:.3f}")
    
    plt.tight_layout()
    ruta = "datos/processed/reportes/curva_iv_pv_validacion.png"
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(ruta, dpi=300, bbox_inches="tight")
    print(f"\nFigura guardada: {ruta}")
    plt.close()

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    from pathlib import Path
    
    ejecutar_pruebas()
    ejemplo_con_figura()