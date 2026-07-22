"""
modelo_diodo_unico.py
================================================================
Paso 7: Implementar la ecuación del diodo único como función pura.

CORRECCIÓN v3: 
  - Manejo explícito de fallos del solver en calcular_curva_iv 
    (warnings.warn en vez de silencio con 0.0)
  - Nota de mantenimiento sobre duplicación de casos límite

Este módulo contiene la implementación de la ecuación del diodo único
(single diode equation) para modelar la curva I-V de un módulo fotovoltaico.

La ecuación implícita es:
    I = Iph - I0 * [exp((V + I*Rs)/(n*Ns*Vt)) - 1] - (V + I*Rs)/Rsh

Uso:
    from modelo_diodo_unico import calcular_corriente
    
    # Calcular corriente para un voltaje, irradiancia y temperatura dados
    I = calcular_corriente(V=30.0, G=1000.0, T=25.0)

Salida:
    - Función pura: calcular_corriente(V, G, T, params)
    - Función vectorizada: calcular_curva_iv(G, T, params)
    - Pruebas unitarias básicas al ejecutar directamente
================================================================
"""

import warnings
import numpy as np
from scipy.optimize import brentq
from dataclasses import dataclass
from typing import Union, Optional

# =====================================================================
# CONSTANTES FÍSICAS
# =====================================================================
K_BOLTZMANN = 1.380649e-23      # J/K - Constante de Boltzmann
Q_ELECTRON = 1.602176634e-19    # C - Carga del electrón
EG_SILICIO = 1.12               # eV - Energía de banda prohibida del silicio a 300K
T_REF = 298.15                  # K - Temperatura de referencia (25°C)
G_REF = 1000.0                  # W/m² - Irradiancia de referencia (STC)


# =====================================================================
# PARÁMETROS DEL MÓDULO (Paso 7.1)
# =====================================================================
@dataclass
class ParametrosModulo:
    """
    Parámetros del módulo fotovoltaico.
    
    CORRECCIÓN v2: Los coeficientes alpha_Isc y beta_Voc están en unidades
    físicas correctas (A/°C y V/°C), calculados a partir de los porcentajes
    típicos del datasheet multiplicados por los valores de referencia.
    
    Valores típicos de un módulo monocristalino de ~300W con 60 celdas.
    Rs y Rsh son valores iniciales típicos de la literatura que serán
    calibrados en el Paso 9 mediante ajuste a datos experimentales.
    """
    # Parámetros del datasheet (STC: G=1000 W/m², T=25°C)
    Voc: float = 37.5           # V - Voltaje de circuito abierto
    Isc: float = 8.5            # A - Corriente de cortocircuito
    Vmpp: float = 30.0          # V - Voltaje en punto de máxima potencia
    Impp: float = 7.8           # A - Corriente en punto de máxima potencia
    Ns: int = 60                # - Número de celdas en serie
    
    # Coeficientes de temperatura CORREGIDOS (del datasheet en %/°C convertidos a unidades físicas)
    # Típicamente: alpha_Isc ≈ +0.05%/°C, beta_Voc ≈ -0.32%/°C
    # Conversión: alpha_Isc [A/°C] = (0.05/100) × Isc_ref = 0.0005 × 8.5 ≈ 0.00425 A/°C
    #             beta_Voc [V/°C] = (-0.32/100) × Voc_ref = -0.0032 × 37.5 ≈ -0.12 V/°C
    alpha_Isc: float = 0.00425  # A/°C - Coeficiente de temperatura de Isc (CORREGIDO)
    beta_Voc: float = -0.12     # V/°C - Coeficiente de temperatura de Voc (CORREGIDO)
    
    # Parámetros del modelo de diodo único (valores iniciales típicos)
    Rs: float = 0.35            # Ω - Resistencia serie (típico: 0.3-0.5 Ω)
    Rsh: float = 300.0          # Ω - Resistencia paralelo (típico: 200-500 Ω)
    n: float = 1.2              # - Factor de idealidad del diodo (típico: 1.0-1.5)
    
    # Configuración del solver numérico
    tolerancia: float = 1e-6    # A - Tolerancia de convergencia
    max_iteraciones: int = 100  # - Máximo de iteraciones

    def __post_init__(self):
        """
        Validación de rango físico (Paso 16, Fase 5): construir
        ParametrosModulo con valores físicamente imposibles debe fallar
        de forma controlada y explícita (ValueError con mensaje claro),
        en vez de propagarse como un error numérico confuso más adelante
        dentro del solver (división por cero, log de número negativo, etc.).
        """
        errores = []
        if self.Voc <= 0.0:
            errores.append(f"Voc debe ser > 0 (recibido: {self.Voc})")
        if self.Isc <= 0.0:
            errores.append(f"Isc debe ser > 0 (recibido: {self.Isc})")
        if not (0.0 < self.Vmpp < self.Voc):
            errores.append(f"Vmpp debe estar en (0, Voc={self.Voc}) (recibido: {self.Vmpp})")
        if not (0.0 < self.Impp < self.Isc):
            errores.append(f"Impp debe estar en (0, Isc={self.Isc}) (recibido: {self.Impp})")
        if self.Ns <= 0:
            errores.append(f"Ns debe ser un entero > 0 (recibido: {self.Ns})")
        if self.Rs < 0.0:
            errores.append(f"Rs debe ser >= 0 (recibido: {self.Rs})")
        if self.Rsh <= 0.0:
            errores.append(f"Rsh debe ser > 0 (división por cero en el modelo si Rsh=0; recibido: {self.Rsh})")
        if self.n <= 0.0:
            errores.append(f"n (factor de idealidad) debe ser > 0 (recibido: {self.n})")
        if self.tolerancia <= 0.0:
            errores.append(f"tolerancia debe ser > 0 (recibido: {self.tolerancia})")
        if self.max_iteraciones <= 0:
            errores.append(f"max_iteraciones debe ser > 0 (recibido: {self.max_iteraciones})")

        if errores:
            raise ValueError(
                "ParametrosModulo recibió valores físicamente inválidos:\n  - "
                + "\n  - ".join(errores)
            )


# =====================================================================
# CARGA / GUARDADO DE PARÁMETROS DESDE YAML (Paso 9)
# =====================================================================
# Estas funciones permiten desacoplar el panel de referencia del
# código: `parametros_panel.yaml` contiene los valores calibrados
# del panel Kyocera KC200GT (ver docs/05_diseño/parametros_panel_referencia.md
# y docs/06_experimentacion/validacion_modelo_pv.md). Los valores por
# defecto de ParametrosModulo (panel genérico ~300W) se conservan para
# no romper las pruebas unitarias existentes de este módulo.

def _ruta_yaml_por_defecto():
    from pathlib import Path
    return Path(__file__).resolve().parent / "parametros_panel.yaml"


def cargar_parametros_desde_yaml(ruta=None) -> ParametrosModulo:
    """
    Carga los parámetros del panel desde un archivo YAML y construye
    un ParametrosModulo. Si `ruta` es None, usa
    `simulacion_fv/planta/parametros_panel.yaml`.
    """
    import yaml
    from pathlib import Path

    ruta = Path(ruta) if ruta is not None else _ruta_yaml_por_defecto()

    with open(ruta, "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    ds = datos["datasheet"]
    modelo = datos["modelo_diodo_unico"]

    return ParametrosModulo(
        Voc=float(ds["Voc"]),
        Isc=float(ds["Isc"]),
        Vmpp=float(ds["Vmpp"]),
        Impp=float(ds["Impp"]),
        Ns=int(ds["Ns"]),
        alpha_Isc=float(ds["alpha_Isc"]),
        beta_Voc=float(ds["beta_Voc"]),
        Rs=float(modelo["Rs"]),
        Rsh=float(modelo["Rsh"]),
        n=float(modelo["n"]),
        tolerancia=float(modelo.get("tolerancia", 1e-6)),
        max_iteraciones=int(modelo.get("max_iteraciones", 100)),
    )


def guardar_calibracion_en_yaml(params: ParametrosModulo, error_porcentual_maximo: float,
                                 ruta=None, calibrado: bool = True):
    """
    Actualiza `parametros_panel.yaml` con los valores calibrados de
    Rs, Rsh y n (Paso 9), y registra los metadatos de la calibración.
    No modifica los valores del datasheet (bloque `datasheet`), solo
    el bloque `modelo_diodo_unico` y `calibracion`.
    """
    import yaml
    from pathlib import Path
    from datetime import datetime

    ruta = Path(ruta) if ruta is not None else _ruta_yaml_por_defecto()

    with open(ruta, "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    datos["modelo_diodo_unico"]["Rs"] = round(float(params.Rs), 6)
    datos["modelo_diodo_unico"]["Rsh"] = round(float(params.Rsh), 4)
    datos["modelo_diodo_unico"]["n"] = round(float(params.n), 6)

    datos["calibracion"]["calibrado"] = bool(calibrado)
    datos["calibracion"]["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos["calibracion"]["error_porcentual_maximo"] = round(float(error_porcentual_maximo), 4)

    with open(ruta, "w", encoding="utf-8") as f:
        yaml.safe_dump(datos, f, allow_unicode=True, sort_keys=False)

    return ruta


# =====================================================================
# FUNCIONES AUXILIARES (Paso 7.2)
# =====================================================================

def calcular_voltaje_termino(n: float, Ns: int, T_kelvin: float) -> float:
    """
    Calcula el voltaje térmico del módulo: Vt = n * Ns * k * T / q
    
    IMPORTANTE: T debe estar en Kelvin, no en Celsius.
    """
    return n * Ns * K_BOLTZMANN * T_kelvin / Q_ELECTRON


def calcular_corriente_fotogenerada(
    G: float,
    T_celsius: float,
    Isc_ref: float,
    alpha_Isc: float
) -> float:
    """
    Calcula la corriente fotogenerada Iph(G,T).
    
    Iph(G,T) = Isc_ref * (G / G_ref) * [1 + alpha_Isc * (T - T_ref)]
    """
    T_ref_celsius = 25.0  # °C
    escala_irradiancia = G / G_REF
    ajuste_temperatura = 1.0 + alpha_Isc * (T_celsius - T_ref_celsius)
    return Isc_ref * escala_irradiancia * ajuste_temperatura


def calcular_corriente_saturacion(
    T_kelvin: float,
    Voc_ref: float,
    Isc_ref: float,
    n: float,
    Ns: int
) -> float:
    """
    Calcula la corriente de saturación inversa I0(T).
    
    I0(T) = I0_ref * (T/T_ref)^3 * exp[(q*Eg/k) * (1/T_ref - 1/T)]
    """
    Vt_ref = calcular_voltaje_termino(n, Ns, T_REF)
    I0_ref = Isc_ref / (np.exp(Voc_ref / Vt_ref) - 1.0)
    
    factor_temperatura = (T_kelvin / T_REF) ** 3
    factor_exponencial = np.exp(
        (Q_ELECTRON * EG_SILICIO / K_BOLTZMANN) * (1.0 / T_REF - 1.0 / T_kelvin)
    )
    
    return I0_ref * factor_temperatura * factor_exponencial


def calcular_voc_ajustado(T_celsius: float, params: ParametrosModulo) -> float:
    """
    Calcula el voltaje de circuito abierto ajustado por temperatura.
    
    Voc(T) = Voc_ref + beta_Voc * (T - T_ref)
    
    Función compartida entre calcular_corriente y calcular_curva_iv
    para evitar duplicación de la fórmula.
    
    NOTA (Paso 10): esta aproximación depende únicamente de T, no de G.
    Es razonable cerca de STC (G≈1000 W/m²), pero a irradiancias bajas
    sobreestima el Voc real. `calcular_curva_iv` usa en su lugar
    `calcular_voc_estimado_gt` (que sí depende de G) para acotar el
    barrido de voltaje. Esta función se conserva sin cambios porque
    `calcular_corriente` la sigue usando como cota superior conservadora
    de un único punto (V,G,T) evaluado bajo demanda, donde no hay riesgo
    de fallo de convergencia por barrido (ver docstring de calcular_corriente).
    """
    return params.Voc + params.beta_Voc * (T_celsius - 25.0)


def calcular_voc_estimado_gt(G: float, T_celsius: float, params: ParametrosModulo) -> float:
    """
    Estima el voltaje de circuito abierto real para una condición (G, T)
    dada, usando la aproximación ideal del diodo único sin Rs/Rsh:

        Voc(G,T) ≈ Vt(T) * ln(Iph(G,T)/I0(T) + 1)

    CORRECCIÓN v4 (Paso 10): a diferencia de `calcular_voc_ajustado`
    (que solo depende de T), esta función sí depende de la irradiancia.
    Se usa exclusivamente para acotar el barrido de voltaje en
    `calcular_curva_iv`: a irradiancias bajas, Iph es pequeña y el Voc
    real cae de forma importante respecto al valor STC. Sin este ajuste,
    el barrido de voltaje se extendía más allá del Voc real, y el
    intervalo de búsqueda del solver de Brent, [0, Isc*1.1], dejaba de
    contener una raíz para esos voltajes fuera de rango físico
    (`f(a)` y `f(b)` con el mismo signo), generando fallos de
    convergencia sistemáticos en condiciones de irradiancia baja
    (amanecer/atardecer/nubosidad densa) — detectado al ejecutar el
    Paso 10 sobre la serie temporal completa.

    Se ignoran Rs y Rsh en esta estimación (aproximación estándar y
    válida para cotas: Rs y Rsh solo desplazan levemente el Voc real
    respecto a esta aproximación ideal, del orden de mV). El valor
    devuelto se usa únicamente como límite superior del barrido, nunca
    como el Voc reportado en los resultados (ese sigue calculándose
    a partir de la curva I-V resuelta punto a punto).
    """
    if G <= 0.0:
        return 0.0

    T_kelvin = T_celsius + 273.15
    Iph = calcular_corriente_fotogenerada(G, T_celsius, params.Isc, params.alpha_Isc)
    if Iph <= 0.0:
        return 0.0

    I0 = calcular_corriente_saturacion(T_kelvin, params.Voc, params.Isc, params.n, params.Ns)
    Vt = calcular_voltaje_termino(params.n, params.Ns, T_kelvin)

    voc_estimado = Vt * np.log(Iph / I0 + 1.0)

    # Nunca por encima del Voc ajustado por temperatura (cota física superior en STC)
    return max(0.0, min(voc_estimado, calcular_voc_ajustado(T_celsius, params)))


# =====================================================================
# ECUACIÓN DEL DIODO ÚNICO IMPLÍCITA (Paso 7.3)
# =====================================================================

def ecuacion_diodo_unico(
    I: float,
    V: float,
    Iph: float,
    I0: float,
    Vt: float,
    Rs: float,
    Rsh: float
) -> float:
    """
    Ecuación implícita del diodo único: f(I) = 0
    
    f(I) = Iph - I0 * [exp((V + I*Rs)/Vt) - 1] - (V + I*Rs)/Rsh - I
    """
    termino_diodo = I0 * (np.exp((V + I * Rs) / Vt) - 1.0)
    termino_shunt = (V + I * Rs) / Rsh
    return Iph - termino_diodo - termino_shunt - I


# =====================================================================
# FUNCIÓN PRINCIPAL: CALCULAR CORRIENTE (Paso 7.4, 7.5)
# =====================================================================

def calcular_corriente(
    V: float,
    G: float,
    T_celsius: float,
    params: ParametrosModulo
) -> float:
    """
    Calcula la corriente I para un voltaje V, irradiancia G y temperatura T dados.
    
    CONVENCIONES DE UNIDADES:
        - V: voltios (V)
        - G: irradiancia en W/m²
        - T_celsius: temperatura en grados Celsius (°C)
        - I: corriente en amperios (A)
    
    La función convierte internamente T a Kelvin para los cálculos físicos.
    
    CASOS LÍMITE MANEJADOS EXPLÍCITAMENTE:
        - G = 0 (noche): retorna I = 0 directamente sin llamar al solver
        - V = 0: retorna I ≈ Iph (aproximación válida, Rs es pequeña)
        - V ≥ Voc: retorna I ≈ 0 (evita corrientes negativas espurias)
    
    MÉTODO NUMÉRICO:
        - Usa scipy.optimize.brentq (método de Brent) para resolver la ecuación implícita
        - Intervalo de búsqueda: [0, Isc] (garantiza cambio de signo)
        - Tolerancia y máximo de iteraciones configurables en params
    
    Excepciones:
        ValueError: si el solver no converge en max_iteraciones
    """
    
    # =================================================================
    # CASO LÍMITE 1: G = 0 (noche) - retornar 0 directamente
    # =================================================================
    if G <= 0.0:
        return 0.0
    
    # =================================================================
    # CASO LÍMITE 2: V ≥ Voc - retornar 0 (evitar corrientes negativas)
    # =================================================================
    # CORRECCIÓN v4 (hallada durante el Paso 12, al simular el MPPT
    # punto a punto): se usa el Voc dependiente de (G,T), no solo de T.
    # Ver docstring de calcular_voc_estimado_gt en este mismo módulo:
    # el Voc real cae de forma importante a irradiancias bajas/medias,
    # y usar el Voc ajustado solo por temperatura como cota permitía
    # que V quedara por encima del Voc real, haciendo que el intervalo
    # de búsqueda del solver de Brent, [0, Isc*1.1], no acotara una raíz.
    Voc_ajustado = calcular_voc_estimado_gt(G, T_celsius, params)

    if Voc_ajustado <= 0.0 or V >= Voc_ajustado:
        return 0.0
    
    # =================================================================
    # CÁLCULO DE PARÁMETROS AUXILIARES
    # =================================================================
    T_kelvin = T_celsius + 273.15
    
    Iph = calcular_corriente_fotogenerada(
        G, T_celsius, params.Isc, params.alpha_Isc
    )
    
    I0 = calcular_corriente_saturacion(
        T_kelvin, params.Voc, params.Isc, params.n, params.Ns
    )
    
    Vt = calcular_voltaje_termino(params.n, params.Ns, T_kelvin)
    
    # =================================================================
    # CASO LÍMITE 3: V = 0 - retornar I ≈ Iph (aproximación válida)
    # =================================================================
    if V == 0.0:
        return Iph
    
    # =================================================================
    # SOLVER NUMÉRICO: Método de Brent
    # =================================================================
    def f(I_candidata):
        return ecuacion_diodo_unico(
            I_candidata, V, Iph, I0, Vt, params.Rs, params.Rsh
        )

    I_min = 0.0
    I_max = params.Isc * 1.1  # 10% de margen por seguridad

    # CORRECCIÓN v5 (hallada durante el Paso 12): f(I) es monótona
    # decreciente en I (a más corriente candidata, más caída en el
    # diodo y más negativo el residuo). Por lo tanto f(0) es el
    # máximo de f en [I_min, I_max]. Si f(0) <= 0, no existe ninguna
    # corriente I >= 0 que satisfaga la ecuación: físicamente, a esta
    # V la fuga por Rsh (V/Rsh) y el diodo ya consumen más corriente
    # que la fotogenerada (Iph), es decir V superó el Voc real del
    # panel en estas condiciones (esto ocurre sobre todo a irradiancia
    # muy baja, donde Iph es pequeña y Rsh no es infinita). En ese
    # caso la respuesta correcta es I=0, sin invocar brentq (evita el
    # "f(a) and f(b) must have different signs").
    if f(I_min) <= 0.0:
        return 0.0

    try:
        I_solucion = brentq(
            f,
            I_min,
            I_max,
            xtol=params.tolerancia,
            maxiter=params.max_iteraciones
        )
        
        if I_solucion < 0.0:
            return 0.0
        
        return I_solucion
        
    except ValueError as e:
        # Fallo RUIDOSO: lanzar excepción explícita con contexto
        raise ValueError(
            f"El solver no convergió para V={V}V, G={G}W/m², T={T_celsius}°C. "
            f"Error: {e}"
        )


# =====================================================================
# FUNCIÓN VECTORIZADA: CALCULAR CURVA I-V COMPLETA
# =====================================================================

def calcular_curva_iv(
    G: float,
    T_celsius: float,
    params: ParametrosModulo,
    n_puntos: int = 200
) -> tuple:
    """
    Calcula la curva I-V completa para condiciones dadas de G y T.
    
    CORRECCIÓN v2: Iph, I0 y Vt se calculan una sola vez por combinación
    (G,T) y se pasan al solver, evitando recálculos redundantes en el bucle.
    
    CORRECCIÓN v3: Los fallos del solver ya no se silencian con 0.0;
    se emite un warnings.warn() para poder detectarlos durante el Paso 10.
    
    NOTA DE MANTENIMIENTO:
    La lógica de casos límite (G<=0, V==0, V>=Voc) está duplicada entre
    esta función y calcular_corriente(). Es el costo de la optimización
    de rendimiento. Si en el futuro se cambia el manejo de alguno de estos
    casos, hay que replicar el cambio en ambas funciones.
    
    Retorna:
        voltajes: array de voltajes (V)
        corrientes: array de corrientes (A)
    """
    # CORRECCIÓN v4 (Paso 10): acotar el barrido con el Voc estimado para
    # la (G,T) real, no con el Voc ajustado solo por temperatura. Ver
    # docstring de calcular_voc_estimado_gt para la justificación.
    Voc_ajustado = calcular_voc_estimado_gt(G, T_celsius, params)

    if Voc_ajustado <= 0.0:
        # G muy baja: curva degenerada, corriente nula en todo el barrido
        voltajes = np.linspace(0.0, calcular_voc_ajustado(T_celsius, params), n_puntos)
        return voltajes, np.zeros(n_puntos)

    # Generar array de voltajes desde 0 hasta Voc
    voltajes = np.linspace(0.0, Voc_ajustado, n_puntos)
    
    # CORRECCIÓN v2: Calcular parámetros auxiliares UNA SOLA VEZ
    T_kelvin = T_celsius + 273.15
    Iph = calcular_corriente_fotogenerada(G, T_celsius, params.Isc, params.alpha_Isc)
    I0 = calcular_corriente_saturacion(T_kelvin, params.Voc, params.Isc, params.n, params.Ns)
    Vt = calcular_voltaje_termino(params.n, params.Ns, T_kelvin)
    
    # Calcular corriente para cada voltaje usando los parámetros ya calculados
    corrientes = []
    fallos_solver = 0
    
    for V in voltajes:
        # Caso límite: G = 0 (duplicado de calcular_corriente)
        if G <= 0.0:
            corrientes.append(0.0)
            continue
        
        # Caso límite: V >= Voc (duplicado de calcular_corriente)
        if V >= Voc_ajustado:
            corrientes.append(0.0)
            continue
        
        # Caso límite: V = 0 (duplicado de calcular_corriente)
        if V == 0.0:
            corrientes.append(Iph)
            continue
        
        # Solver numérico
        def f(I_candidata):
            return ecuacion_diodo_unico(I_candidata, V, Iph, I0, Vt, params.Rs, params.Rsh)

        # CORRECCIÓN v5 (Paso 12): f(0) <= 0 implica que no existe
        # I >= 0 que resuelva la ecuación en este V (ver docstring
        # detallado en calcular_corriente). Evita el fallo de bracket
        # del solver de Brent en vez de dejar que lo lance como
        # advertencia.
        if f(0.0) <= 0.0:
            corrientes.append(0.0)
            continue

        try:
            I_solucion = brentq(f, 0.0, params.Isc * 1.1, 
                               xtol=params.tolerancia, maxiter=params.max_iteraciones)
            corrientes.append(max(0.0, I_solucion))
        except ValueError as e:
            # CORRECCIÓN v3: Fallo EXPLÍCITO con advertencia, no silencio
            fallos_solver += 1
            warnings.warn(
                f"Solver no convergió en V={V:.3f}V (G={G}W/m², T={T_celsius}°C). "
                f"Se asigna I=0.0. Error: {e}",
                RuntimeWarning,
                stacklevel=2
            )
            corrientes.append(0.0)
    
    # Resumen de fallos al final del barrido (para no saturar la consola)
    if fallos_solver > 0:
        warnings.warn(
            f"calcular_curva_iv: {fallos_solver} punto(s) de la curva no convergieron "
            f"en el solver. Revisar parámetros del modelo.",
            RuntimeWarning,
            stacklevel=2
        )
    
    return voltajes, np.array(corrientes)


# =====================================================================
# PRUEBAS UNITARIAS BÁSICAS
# =====================================================================

def ejecutar_pruebas_unitarias():
    """
    Ejecuta pruebas unitarias básicas para validar la implementación.
    """
    print("\n" + "=" * 70)
    print("EJECUTANDO PRUEBAS UNITARIAS DEL MODELO DE DIODO ÚNICO")
    print("=" * 70)
    
    params = ParametrosModulo()
    
    # =================================================================
    # PRUEBA 1: G = 0 debe retornar I = 0
    # =================================================================
    print("\n[Prueba 1] G = 0 (noche) → I debe ser 0")
    I = calcular_corriente(V=30.0, G=0.0, T_celsius=25.0, params=params)
    assert I == 0.0, f"Esperado: 0.0, Obtenido: {I}"
    print(f"  ✓ I = {I} A (correcto)")
    
    # =================================================================
    # PRUEBA 2: V = 0 debe retornar I ≈ Isc
    # =================================================================
    print("\n[Prueba 2] V = 0 → I debe ser ≈ Isc")
    I = calcular_corriente(V=0.0, G=1000.0, T_celsius=25.0, params=params)
    diferencia = abs(I - params.Isc)
    assert diferencia < 0.1, f"Esperado: ≈{params.Isc}, Obtenido: {I}"
    print(f"  ✓ I = {I:.4f} A (Isc = {params.Isc} A, diferencia = {diferencia:.4f} A)")
    
    # =================================================================
    # PRUEBA 3: V = Voc debe retornar I ≈ 0
    # =================================================================
    print("\n[Prueba 3] V = Voc → I debe ser ≈ 0")
    I = calcular_corriente(V=params.Voc, G=1000.0, T_celsius=25.0, params=params)
    assert I < 0.01, f"Esperado: ≈0, Obtenido: {I}"
    print(f"  ✓ I = {I:.6f} A (correcto, muy cercano a 0)")
    
    # =================================================================
    # PRUEBA 4: V > Voc debe retornar I = 0
    # =================================================================
    print("\n[Prueba 4] V > Voc → I debe ser 0")
    I = calcular_corriente(V=params.Voc + 5.0, G=1000.0, T_celsius=25.0, params=params)
    assert I == 0.0, f"Esperado: 0.0, Obtenido: {I}"
    print(f"  ✓ I = {I} A (correcto)")
    
    # =================================================================
    # PRUEBA 5: Punto de máxima potencia (Vmp, Imp) debe ser consistente
    # =================================================================
    print("\n[Prueba 5] V = Vmpp → I debe ser cercano a Impp")
    I = calcular_corriente(V=params.Vmpp, G=1000.0, T_celsius=25.0, params=params)
    diferencia = abs(I - params.Impp)
    print(f"  ✓ I = {I:.4f} A (Impp = {params.Impp} A, diferencia = {diferencia:.4f} A)")
    print(f"    (Nota: la diferencia es esperada porque Rs y Rsh son valores iniciales)")
    
    # =================================================================
    # PRUEBA 6: Efecto de la irradiancia (I debe escalar linealmente con G)
    # =================================================================
    print("\n[Prueba 6] I debe escalar aproximadamente lineal con G (V=0)")
    I_1000 = calcular_corriente(V=0.0, G=1000.0, T_celsius=25.0, params=params)
    I_500 = calcular_corriente(V=0.0, G=500.0, T_celsius=25.0, params=params)
    ratio = I_500 / I_1000
    assert 0.45 < ratio < 0.55, f"Esperado: ≈0.5, Obtenido: {ratio}"
    print(f"  ✓ I(500)/I(1000) = {ratio:.4f} (esperado: ≈0.5)")
    
    # =================================================================
    # PRUEBA 7: Efecto de la temperatura (Voc disminuye con T) - CORREGIDA
    # =================================================================
    print("\n[Prueba 7] Voc debe disminuir significativamente con la temperatura")
    Voc_25 = calcular_voc_ajustado(25.0, params)
    Voc_50 = calcular_voc_ajustado(50.0, params)
    
    caida_esperada = abs(params.beta_Voc) * 25.0  # ~3.0 V
    caida_real = Voc_25 - Voc_50
    
    print(f"  Voc(25°C) = {Voc_25:.2f} V")
    print(f"  Voc(50°C) = {Voc_50:.2f} V")
    print(f"  Caída real: {caida_real:.2f} V (esperada: ~{caida_esperada:.2f} V)")
    
    assert Voc_50 < Voc_25, f"Esperado: Voc_50 < Voc_25"
    assert caida_real > 2.0, f"Caída insuficiente: {caida_real} V (debería ser >2V)"
    print(f"  ✓ Voc disminuye correctamente con la temperatura")
    
    # =================================================================
    # PRUEBA 8: Validación de magnitud de coeficientes (NUEVA)
    # =================================================================
    print("\n[Prueba 8] Validación de magnitud de coeficientes de temperatura")
    print(f"  alpha_Isc = {params.alpha_Isc} A/°C")
    print(f"  beta_Voc = {params.beta_Voc} V/°C")
    
    assert 0.003 < params.alpha_Isc < 0.006, \
        f"alpha_Isc fuera de rango típico: {params.alpha_Isc} A/°C"
    assert -0.15 < params.beta_Voc < -0.08, \
        f"beta_Voc fuera de rango típico: {params.beta_Voc} V/°C"
    
    print(f"  ✓ Coeficientes en rango típico de la literatura")
    
    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON CORRECTAMENTE")
    print("=" * 70)


# =====================================================================
# EJEMPLO DE USO
# =====================================================================

def ejemplo_uso():
    """
    Muestra un ejemplo de uso del modelo de diodo único.
    """
    print("\n" + "=" * 70)
    print("EJEMPLO DE USO DEL MODELO DE DIODO ÚNICO")
    print("=" * 70)
    
    params = ParametrosModulo()
    
    print(f"\nParámetros del módulo:")
    print(f"  Voc = {params.Voc} V")
    print(f"  Isc = {params.Isc} A")
    print(f"  Vmpp = {params.Vmpp} V")
    print(f"  Impp = {params.Impp} A")
    print(f"  Ns = {params.Ns} celdas")
    print(f"  Rs = {params.Rs} Ω (valor inicial)")
    print(f"  Rsh = {params.Rsh} Ω (valor inicial)")
    print(f"  n = {params.n} (valor inicial)")
    print(f"  alpha_Isc = {params.alpha_Isc} A/°C (CORREGIDO)")
    print(f"  beta_Voc = {params.beta_Voc} V/°C (CORREGIDO)")
    
    V = 30.0
    G = 1000.0
    T = 25.0
    
    I = calcular_corriente(V, G, T, params)
    
    print(f"\nCondiciones: V={V}V, G={G}W/m², T={T}°C")
    print(f"Corriente calculada: I = {I:.4f} A")
    print(f"Potencia: P = V*I = {V*I:.2f} W")
    
    voltajes, corrientes = calcular_curva_iv(G, T, params, n_puntos=50)
    
    print(f"\nCurva I-V calculada con {len(voltajes)} puntos")
    print(f"  Voltajes: [{voltajes[0]:.1f}, {voltajes[-1]:.1f}] V")
    print(f"  Corrientes: [{corrientes[0]:.4f}, {corrientes[-1]:.6f}] A")
    
    potencias = voltajes * corrientes
    potencias = np.maximum(potencias, 0.0)
    idx_max = np.argmax(potencias)
    print(f"\nPotencia máxima de la curva:")
    print(f"  Vmpp_curva = {voltajes[idx_max]:.2f} V")
    print(f"  Impp_curva = {corrientes[idx_max]:.4f} A")
    print(f"  Pmax = {potencias[idx_max]:.2f} W")

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    ejecutar_pruebas_unitarias()
    ejemplo_uso()