"""
validacion_modelo_stc.py
================================================================
Paso 9: Validar el modelo de diodo único contra el datasheet.

Ejecuta el modelo del panel de referencia (Kyocera KC200GT, ver
simulacion_fv/planta/parametros_panel.yaml) en condiciones estándar
de prueba (STC: 1000 W/m², 25°C) y compara Voc, Isc, Vmpp e Impp
calculados contra los valores del datasheet.

Si el error de alguno de los cuatro valores supera el margen
aceptado (2-3%), se ejecuta una calibración numérica de los
parámetros que NO vienen del datasheet (Rs, Rsh, n) mediante
mínimos cuadrados no lineales (scipy.optimize.least_squares),
y se guarda el resultado calibrado de vuelta en
`parametros_panel.yaml`.

Uso:
    python simulacion_fv/pruebas/validacion_modelo_stc.py

Salida:
    - simulacion_fv/planta/parametros_panel.yaml actualizado (Rs, Rsh, n calibrados)
    - docs/06_experimentacion/validacion_modelo_pv.md (reporte de validación)
    - datos/processed/reportes/curva_iv_pv_kc200gt_calibrado.png
================================================================
"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy.optimize import least_squares

# Permite importar los módulos de simulacion_fv/planta sin instalar el paquete
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROYECTO / "simulacion_fv" / "planta"))

from modelo_diodo_unico import (          # noqa: E402
    ParametrosModulo,
    calcular_corriente,
    calcular_curva_iv,
    calcular_voc_ajustado,
    cargar_parametros_desde_yaml,
    guardar_calibracion_en_yaml,
)
from curva_caracteristica import generar_curva_iv_pv, graficar_curva_iv_pv  # noqa: E402

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
MARGEN_ERROR_ACEPTABLE = 1.0  # % - por encima de esto se dispara la calibración
# Nota: la guía metodológica admite un margen de 2-3%. Se exige aquí un
# margen más estricto (1%) de forma deliberada: el error inicial con los
# parámetros de la literatura (Rs=0.221, Rsh=415.4, n=1.2) ya es de 2.18%
# en Vmpp, dentro del rango "aceptable" de la guía pero mejorable. Forzar
# la calibración documenta el proceso completo de ajuste (Paso 9) y deja
# un modelo con mayor fidelidad al datasheet para las fases siguientes.
RUTA_YAML = RAIZ_PROYECTO / "simulacion_fv" / "planta" / "parametros_panel.yaml"
RUTA_REPORTE = RAIZ_PROYECTO / "docs" / "06_experimentacion" / "validacion_modelo_pv.md"
RUTA_FIGURA = RAIZ_PROYECTO / "datos" / "processed" / "reportes" / "curva_iv_pv_kc200gt_calibrado.png"


# =====================================================================
# 1. EVALUACIÓN DEL MODELO EN STC
# =====================================================================
def evaluar_modelo_stc(params: ParametrosModulo) -> dict:
    """
    Calcula Voc, Isc, Vmpp, Impp del modelo en STC (G=1000, T=25) y
    los compara contra los valores objetivo del datasheet (guardados
    en la misma instancia de ParametrosModulo).
    """
    G, T = 1000.0, 25.0

    Voc_modelo = calcular_voc_ajustado(T, params)
    Isc_modelo = calcular_corriente(V=0.0, G=G, T_celsius=T, params=params)

    voltajes, corrientes = calcular_curva_iv(G, T, params, n_puntos=400)
    potencias = np.maximum(voltajes * corrientes, 0.0)
    idx_max = int(np.argmax(potencias))
    Vmpp_modelo = float(voltajes[idx_max])
    Impp_modelo = float(corrientes[idx_max])

    objetivo = {
        "Voc": params.Voc, "Isc": params.Isc,
        "Vmpp": params.Vmpp, "Impp": params.Impp,
    }
    modelo = {
        "Voc": Voc_modelo, "Isc": Isc_modelo,
        "Vmpp": Vmpp_modelo, "Impp": Impp_modelo,
    }
    errores_pct = {
        k: abs(modelo[k] - objetivo[k]) / objetivo[k] * 100.0
        for k in objetivo
    }

    return {"objetivo": objetivo, "modelo": modelo, "errores_pct": errores_pct}


def imprimir_comparacion(resultado: dict, titulo: str):
    print(f"\n{titulo}")
    print(f"  {'Variable':<8}{'Datasheet':>12}{'Modelo':>12}{'Error %':>12}")
    for k in ("Voc", "Isc", "Vmpp", "Impp"):
        print(f"  {k:<8}{resultado['objetivo'][k]:>12.4f}"
              f"{resultado['modelo'][k]:>12.4f}{resultado['errores_pct'][k]:>12.2f}")


# =====================================================================
# 2. CALIBRACIÓN NUMÉRICA DE Rs, Rsh, n (Paso 9)
# =====================================================================
def residuales_calibracion(x, params_base: ParametrosModulo) -> np.ndarray:
    """
    Función de residuales para least_squares. x = [Rs, Rsh, n].
    Los cuatro residuales están normalizados por el valor objetivo
    (error relativo) para que las cuatro magnitudes (V, A) sean
    comparables en la misma escala durante el ajuste.
    """
    Rs, Rsh, n = x

    p = ParametrosModulo(
        Voc=params_base.Voc, Isc=params_base.Isc,
        Vmpp=params_base.Vmpp, Impp=params_base.Impp, Ns=params_base.Ns,
        alpha_Isc=params_base.alpha_Isc, beta_Voc=params_base.beta_Voc,
        Rs=Rs, Rsh=Rsh, n=n,
        tolerancia=params_base.tolerancia, max_iteraciones=params_base.max_iteraciones,
    )

    resultado = evaluar_modelo_stc(p)
    residuales = np.array([
        (resultado["modelo"][k] - resultado["objetivo"][k]) / resultado["objetivo"][k]
        for k in ("Voc", "Isc", "Vmpp", "Impp")
    ])
    return residuales


def calibrar_parametros(params_base: ParametrosModulo) -> tuple:
    """
    Ajusta Rs, Rsh, n mediante mínimos cuadrados no lineales acotados
    (Trust Region Reflective) para minimizar el error relativo frente
    al datasheet. Rangos físicamente razonables tomados de la
    literatura (Villalva et al., 2009; De Soto et al., 2006).
    """
    x0 = np.array([params_base.Rs, params_base.Rsh, params_base.n])
    limites_inferiores = np.array([1e-4, 50.0, 1.0])
    limites_superiores = np.array([2.0, 2000.0, 1.6])

    print("\n--- [Paso 9.2] Calibrando Rs, Rsh, n mediante least_squares ---")
    print(f"  Valores iniciales: Rs={x0[0]:.4f} Ω, Rsh={x0[1]:.2f} Ω, n={x0[2]:.4f}")

    resultado_opt = least_squares(
        residuales_calibracion,
        x0=x0,
        bounds=(limites_inferiores, limites_superiores),
        args=(params_base,),
        xtol=1e-12, ftol=1e-12, gtol=1e-12,
    )

    Rs_cal, Rsh_cal, n_cal = resultado_opt.x
    print(f"  Convergencia: {resultado_opt.success} ({resultado_opt.message})")
    print(f"  Valores calibrados: Rs={Rs_cal:.4f} Ω, Rsh={Rsh_cal:.2f} Ω, n={n_cal:.4f}")

    params_calibrados = ParametrosModulo(
        Voc=params_base.Voc, Isc=params_base.Isc,
        Vmpp=params_base.Vmpp, Impp=params_base.Impp, Ns=params_base.Ns,
        alpha_Isc=params_base.alpha_Isc, beta_Voc=params_base.beta_Voc,
        Rs=float(Rs_cal), Rsh=float(Rsh_cal), n=float(n_cal),
        tolerancia=params_base.tolerancia, max_iteraciones=params_base.max_iteraciones,
    )

    return params_calibrados, resultado_opt


# =====================================================================
# 3. GENERACIÓN DEL REPORTE DE VALIDACIÓN (docs/06_experimentacion/)
# =====================================================================
def generar_reporte_markdown(resultado_inicial: dict, resultado_final: dict,
                              params_finales: ParametrosModulo, calibracion_ejecutada: bool,
                              resultado_opt=None):
    RUTA_REPORTE.parent.mkdir(parents=True, exist_ok=True)

    def tabla(resultado):
        filas = []
        for k in ("Voc", "Isc", "Vmpp", "Impp"):
            filas.append(
                f"| {k} | {resultado['objetivo'][k]:.4f} | "
                f"{resultado['modelo'][k]:.4f} | {resultado['errores_pct'][k]:.3f} % |"
            )
        return "\n".join(filas)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_max_inicial = max(resultado_inicial["errores_pct"].values())
    error_max_final = max(resultado_final["errores_pct"].values())

    contenido = f"""# Validación del modelo de diodo único contra el datasheet
**Paso 9 — Fase 2, Construcción del modelo matemático del panel**

## 1. Objetivo

Verificar que el modelo de diodo único implementado en
`simulacion_fv/planta/modelo_diodo_unico.py` reproduce, en condiciones
estándar de prueba (STC: 1000 W/m², 25 °C), los cuatro valores
eléctricos característicos publicados en el datasheet del panel de
referencia (Kyocera KC200GT — ver
`docs/05_diseño/parametros_panel_referencia.md`): Voc, Isc, Vmpp e Impp.

Fecha de ejecución: {fecha}

## 2. Panel de referencia

| Parámetro | Valor | Unidad |
|---|---|---|
| Modelo | Kyocera KC200GT | — |
| Voc (datasheet) | {params_finales.Voc} | V |
| Isc (datasheet) | {params_finales.Isc} | A |
| Vmpp (datasheet) | {params_finales.Vmpp} | V |
| Impp (datasheet) | {params_finales.Impp} | A |
| Ns | {params_finales.Ns} | celdas |
| alpha_Isc | {params_finales.alpha_Isc} | A/°C |
| beta_Voc | {params_finales.beta_Voc} | V/°C |

## 3. Evaluación inicial (parámetros no calibrados)

Valores iniciales de Rs, Rsh y n tomados de la literatura
(Villalva et al., 2009) antes de cualquier ajuste numérico:

| Variable | Datasheet | Modelo (inicial) | Error |
|---|---|---|---|
{tabla(resultado_inicial)}

**Error porcentual máximo inicial: {error_max_inicial:.3f} %**
**Margen aceptado: {MARGEN_ERROR_ACEPTABLE} %**

"""

    if calibracion_ejecutada:
        contenido += f"""## 4. Proceso de calibración

Dado que el error inicial máximo ({error_max_inicial:.3f} %) supera el
margen aceptado ({MARGEN_ERROR_ACEPTABLE} %), se ajustaron los tres
parámetros del modelo que no provienen directamente del datasheet:
la resistencia serie (Rs), la resistencia paralelo (Rsh) y el factor
de idealidad del diodo (n).

- **Método**: mínimos cuadrados no lineales acotados
  (`scipy.optimize.least_squares`, algoritmo Trust Region Reflective).
- **Función objetivo**: vector de 4 residuales relativos
  `(valor_modelo - valor_datasheet) / valor_datasheet` para
  Voc, Isc, Vmpp e Impp evaluados en STC.
- **Rango de búsqueda**: Rs ∈ [1×10⁻⁴, 2.0] Ω, Rsh ∈ [50, 2000] Ω,
  n ∈ [1.0, 1.6] — rangos físicamente razonables para módulos de
  silicio cristalino según la literatura (Villalva et al., 2009;
  De Soto et al., 2006).
- **Convergencia**: {resultado_opt.success} — {resultado_opt.message}

### Parámetros antes y después de la calibración

| Parámetro | Valor inicial | Valor calibrado |
|---|---|---|
| Rs (Ω) | 0.221 | {params_finales.Rs:.4f} |
| Rsh (Ω) | 415.4 | {params_finales.Rsh:.2f} |
| n | 1.2 | {params_finales.n:.4f} |

## 5. Evaluación final (parámetros calibrados)

| Variable | Datasheet | Modelo (calibrado) | Error |
|---|---|---|---|
{tabla(resultado_final)}

**Error porcentual máximo final: {error_max_final:.3f} %**

"""
    else:
        contenido += f"""## 4. Resultado

El error inicial máximo ({error_max_inicial:.3f} %) ya se encuentra
por debajo del margen aceptado ({MARGEN_ERROR_ACEPTABLE} %), por lo
que **no fue necesario ejecutar la calibración numérica** de Rs,
Rsh y n. Se conservan los valores iniciales tomados de la literatura.

"""

    conclusion = "cumple" if error_max_final <= MARGEN_ERROR_ACEPTABLE else "NO cumple"

    contenido += f"""## 6. Conclusión

El modelo de diodo único, con los parámetros finales registrados en
`simulacion_fv/planta/parametros_panel.yaml`, **{conclusion}** el
criterio de validación establecido (error < {MARGEN_ERROR_ACEPTABLE} %
frente al datasheet) para las cuatro variables eléctricas evaluadas
en STC. Estos parámetros son los que se usan a partir de este punto
para aplicar el modelo sobre toda la serie temporal ambiental
(Paso 10).

## 7. Limitaciones

- La calibración se realiza únicamente en el punto STC (1000 W/m²,
  25 °C). No se dispone de curvas I-V experimentales del panel a
  otras condiciones de irradiancia/temperatura para una calibración
  multi-punto, por lo que Rs, Rsh y n permanecen fijos para todas
  las condiciones simuladas — esta es una simplificación estándar
  en la literatura de modelos de un diodo cuando solo se dispone
  de los cuatro puntos del datasheet.
- El ajuste no es único: distintas combinaciones de (Rs, Rsh, n)
  pueden producir errores similares en los cuatro puntos objetivo
  (el problema está levemente sub-determinado). Se reportan los
  valores obtenidos por el optimizador con la semilla inicial de
  la literatura, sin explorar múltiples inicializaciones.

## 8. Evidencia gráfica

Ver `datos/processed/reportes/curva_iv_pv_kc200gt_calibrado.png`:
curvas I-V y P-V del panel calibrado en STC, con el MPP marcado y
comparado visualmente contra los valores del datasheet.
"""

    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"\n[Paso 9] Reporte de validación guardado en: {RUTA_REPORTE}")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 70)
    print("PASO 9: VALIDACIÓN DEL MODELO DE DIODO ÚNICO CONTRA EL DATASHEET")
    print("=" * 70)

    print(f"\n--- [Paso 9.1] Cargando parámetros desde {RUTA_YAML.name} ---")
    params_iniciales = cargar_parametros_desde_yaml(RUTA_YAML)

    resultado_inicial = evaluar_modelo_stc(params_iniciales)
    imprimir_comparacion(resultado_inicial, "Evaluación inicial (Rs, Rsh, n de la literatura):")

    error_max_inicial = max(resultado_inicial["errores_pct"].values())
    calibracion_ejecutada = error_max_inicial > MARGEN_ERROR_ACEPTABLE

    resultado_opt = None
    if calibracion_ejecutada:
        print(f"\nError máximo inicial ({error_max_inicial:.2f} %) supera el margen "
              f"aceptado ({MARGEN_ERROR_ACEPTABLE} %). Se ejecuta calibración.")
        params_finales, resultado_opt = calibrar_parametros(params_iniciales)
        resultado_final = evaluar_modelo_stc(params_finales)
        imprimir_comparacion(resultado_final, "Evaluación final (Rs, Rsh, n calibrados):")

        error_max_final = max(resultado_final["errores_pct"].values())
        guardar_calibracion_en_yaml(params_finales, error_max_final, ruta=RUTA_YAML, calibrado=True)
        print(f"\n[Paso 9.3] parametros_panel.yaml actualizado con la calibración.")
    else:
        print(f"\nError máximo inicial ({error_max_inicial:.2f} %) dentro del margen "
              f"aceptado ({MARGEN_ERROR_ACEPTABLE} %). No se requiere calibración.")
        params_finales = params_iniciales
        resultado_final = resultado_inicial

    # Reporte markdown para la tesis
    generar_reporte_markdown(resultado_inicial, resultado_final, params_finales,
                              calibracion_ejecutada, resultado_opt)

    # Figura de validación (curva I-V / P-V en STC con parámetros finales)
    print("\n--- [Paso 9.4] Generando figura de validación ---")
    curva = generar_curva_iv_pv(1000.0, 25.0, params_finales)
    RUTA_FIGURA.parent.mkdir(parents=True, exist_ok=True)
    graficar_curva_iv_pv(curva, ruta_guardado=str(RUTA_FIGURA))

    error_max_final = max(resultado_final["errores_pct"].values())
    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: error máximo = {error_max_final:.3f} % "
          f"({'OK' if error_max_final <= MARGEN_ERROR_ACEPTABLE else 'FUERA DE MARGEN'})")
    print("=" * 70)

    assert error_max_final <= MARGEN_ERROR_ACEPTABLE, (
        f"El modelo calibrado no alcanzó el margen de error aceptado: "
        f"{error_max_final:.3f} % > {MARGEN_ERROR_ACEPTABLE} %"
    )


if __name__ == "__main__":
    main()