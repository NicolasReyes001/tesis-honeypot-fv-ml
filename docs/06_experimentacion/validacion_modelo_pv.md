# Validación del modelo de diodo único contra el datasheet
**Paso 9 — Fase 2, Construcción del modelo matemático del panel**

## 1. Objetivo

Verificar que el modelo de diodo único implementado en
`simulacion_fv/planta/modelo_diodo_unico.py` reproduce, en condiciones
estándar de prueba (STC: 1000 W/m², 25 °C), los cuatro valores
eléctricos característicos publicados en el datasheet del panel de
referencia (Kyocera KC200GT — ver
`docs/05_diseño/parametros_panel_referencia.md`): Voc, Isc, Vmpp e Impp.

Fecha de ejecución: 2026-07-21 18:41:28

## 2. Panel de referencia

| Parámetro | Valor | Unidad |
|---|---|---|
| Modelo | Kyocera KC200GT | — |
| Voc (datasheet) | 32.9 | V |
| Isc (datasheet) | 8.21 | A |
| Vmpp (datasheet) | 26.3 | V |
| Impp (datasheet) | 7.61 | A |
| Ns | 72 | celdas |
| alpha_Isc | 0.0026 | A/°C |
| beta_Voc | -0.126 | V/°C |

## 3. Evaluación inicial (parámetros no calibrados)

Valores iniciales de Rs, Rsh y n tomados de la literatura
(Villalva et al., 2009) antes de cualquier ajuste numérico:

| Variable | Datasheet | Modelo (inicial) | Error |
|---|---|---|---|
| Voc | 32.9000 | 32.9000 | 0.000 % |
| Isc | 8.2100 | 8.2100 | 0.000 % |
| Vmpp | 26.3000 | 26.4684 | 0.640 % |
| Impp | 7.6100 | 7.5815 | 0.374 % |

**Error porcentual máximo inicial: 0.640 %**
**Margen aceptado: 1.0 %**

## 4. Resultado

El error inicial máximo (0.640 %) ya se encuentra
por debajo del margen aceptado (1.0 %), por lo
que **no fue necesario ejecutar la calibración numérica** de Rs,
Rsh y n. Se conservan los valores iniciales tomados de la literatura.

## 6. Conclusión

El modelo de diodo único, con los parámetros finales registrados en
`simulacion_fv/planta/parametros_panel.yaml`, **cumple** el
criterio de validación establecido (error < 1.0 %
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
