# Diseño de la simulación fotovoltaica
**Documento maestro — Paso 18, Fase 5: Documentar supuestos y parámetros usados**

Este documento consolida todas las decisiones de diseño, parámetros y
resultados de la subsimulación fotovoltaica (`simulacion_fv/`),
construida siguiendo la guía metodológica de 18 pasos. Está pensado
para trasladarse directamente al capítulo de metodología de la tesis.

---

## 1. Panel de referencia

| Parámetro            | Valor                  | Fuente                                       |
| -------------------- | ---------------------- | -------------------------------------------- |
| Modelo               | Kyocera KC200GT        | Datasheet oficial (Kyocera Solar Inc., 2010) |
| Potencia nominal     | 200 Wp                 | Datasheet                                    |
| Tecnología           | Silicio policristalino | Datasheet                                    |
| Voc                  | 32.9 V                 | Datasheet                                    |
| Isc                  | 8.21 A                 | Datasheet                                    |
| Vmpp                 | 26.3 V                 | Datasheet                                    |
| Impp                 | 7.61 A                 | Datasheet                                    |
| Ns (celdas en serie) | 72                     | Datasheet                                    |
| alpha_Isc            | +0.0026 A/°C           | Datasheet                                    |
| beta_Voc             | −0.126 V/°C            | Datasheet                                    |

Documentación completa: `docs/05_diseño/parametros_panel_referencia.md`.
Referencia bibliográfica: `referencias/bibliografia.bib` →
`kyocera2010kc200gt`. PDF del datasheet enlazado en
`referencias/papers/DESCARGAR_datasheet_kyocera_kc200gt.url`.

## 2. Fuente de datos ambientales

- **Variables**: irradiancia global horizontal (`ALLSKY_SFC_SW_DWN`,
  W/m²) y temperatura a 2 metros (`T2M`, °C).
- **Fuente**: API NASA POWER, coordenadas de Bogotá, Colombia.
- **Periodo simulado actual**: 1 día representativo (2026-03-01),
  con resolución nativa horaria de la API.
- **Variabilidad sintética de nubosidad** (Paso 6): cadena de Markov
  de 4 estados (despejado, parcialmente nublado, nublado, muy
  nublado) con matriz de transición propia, cada estado con un factor
  de atenuación distinto sobre la irradiancia ideal, más ruido
  gaussiano leve dentro de cada estado.
- **Resolución temporal de trabajo**: 5 minutos, obtenida por
  interpolación temporal desde la resolución horaria nativa.

Documentación completa: `docs/04_metodologia/diseno_dataset.md`.

## 3. Modelo matemático del panel

- **Modelo físico**: diodo único de 5 parámetros (Iph, I0, Rs, Rsh, n),
  ecuación implícita I = Iph − I0·(exp((V+I·Rs)/Vt) − 1) − (V+I·Rs)/Rsh.
- **Método numérico**: resolución punto a punto con el método de
  Brent (`scipy.optimize.brentq`), acotado al rango físicamente
  válido de corriente [0, 1.1·Isc].
- **Curva completa**: barrido de voltaje de 0 a Voc (200-400 puntos
  según el uso), con localización del punto de máxima potencia por
  máximo discreto + refinamiento por interpolación parabólica de 3
  puntos.
- **Implementación**: `simulacion_fv/planta/modelo_diodo_unico.py`
  (Paso 7) y `simulacion_fv/planta/curva_caracteristica.py` (Paso 8).
  Ambas funciones son puras (sin efectos secundarios, sin leer
  archivos ni variables globales), por diseño, para poder reutilizarse
  sin cambios cuando se envuelvan en un servicio Modbus/MQTT.
- **Parámetros separados del código**: `simulacion_fv/planta/parametros_panel.yaml`.

## 4. Validación del modelo (Paso 9)

El modelo se evaluó en condiciones estándar de prueba (STC: 1000 W/m²,
25°C) contra los 4 valores del datasheet (Voc, Isc, Vmpp, Impp).

| Etapa                                                   | Error máximo |
| ------------------------------------------------------- | ------------ |
| Con Rs, Rsh, n de la literatura (Villalva et al., 2009) | 2.18%        |
| Tras calibración (`scipy.optimize.least_squares`)       | **0.64%**    |

Parámetros calibrados: Rs=0.1336 Ω, Rsh=1038.43 Ω, n=1.121.

Reporte completo: `docs/06_experimentacion/validacion_modelo_pv.md`.

## 5. Algoritmo de seguimiento del punto de máxima potencia (MPPT)

- **Algoritmo**: Perturbar y Observar (P&O), implementado como
  función de estado pura (`EstadoMPPT` → `EstadoMPPT`), sin barrer
  la curva completa — simula un inversor real que solo conoce el
  voltaje y la potencia del ciclo anterior.
- **Parámetro configurable**: paso de perturbación (`paso_V`).
- **Resultado comparativo** (1 día simulado, 277 instantes a 5 min):

| Configuración               | Eficiencia de captura de energía |
| --------------------------- | -------------------------------- |
| paso_V = 0.1 V (pequeño)    | 91.64%                           |
| paso_V = 0.5 V (intermedio) | 87.54%                           |
| paso_V = 2.0 V (grande)     | 96.44%                           |

Implementación: `simulacion_fv/inversor/mppt_perturbar_observar.py`
(Paso 11), `simular_seguimiento_mppt.py` (Paso 12). Comparación y
discusión completa: `docs/06_experimentacion/eficiencia_mppt.md`
(Paso 13).

## 6. Esquema de datos de salida (Paso 14)

Contrato estable de 6 variables para el consumo futuro por
Modbus/MQTT: `timestamp`, `potencia_dc`, `voltaje_dc`, `corriente_dc`,
`temperatura_panel`, `irradiancia`. Se expone la potencia **seguida
por el MPPT** (realista), no la ideal. Especificación completa:
`docs/05_diseño/esquema_datos_planta.md`.

La función `obtener_estado_actual(timestamp)`
(`simulacion_fv/planta/interfaz_estado_actual.py`, Paso 15) es el
único punto de entrada que en el futuro se envolverá con un servidor
Modbus/MQTT, sin modificar el modelo físico.

## 7. Limitaciones conocidas

1. **Periodo simulado limitado**: el dataset ambiental cubre
   actualmente un único día representativo (2026-03-01), no un año
   completo. Escalar a un periodo más largo es directo con los
   scripts existentes (Fase 1), pero no se ejecutó por alcance/tiempo
   de este trabajo.
2. **Calibración en un único punto**: Rs, Rsh y n se calibraron solo
   contra los 4 valores de datasheet en STC, no contra curvas I-V
   experimentales a múltiples condiciones. Es la práctica estándar
   cuando no se dispone de datos experimentales adicionales, pero
   implica que el modelo es más confiable cerca de STC que en
   condiciones extremas.
3. **Rango de validez térmico**: el modelo es numéricamente estable
   más allá de 65-70°C, pero no fue diseñado ni se pretende que sea
   preciso en ese rango (fuera de las condiciones de operación reales
   esperadas en Bogotá). Ver `simulacion_fv/pruebas/test_modelo_diodo.py`.
4. **Acoplamiento entre el ciclo del MPPT y la resolución de
   muestreo**: el P&O se ejecuta una vez por cada instante ambiental
   (5 min), mientras que un inversor real cicla su lazo MPPT mucho
   más rápido (ms-s). Esto afecta la comparación entre tamaños de
   paso reportada en la sección 5 (ver limitación detallada en
   `eficiencia_mppt.md`).
5. **Sin modelado del inversor DC→AC**: la simulación se detiene en
   la potencia DC de salida del panel/string; la eficiencia de
   conversión DC→AC de un inversor real no está modelada (sería una
   extensión natural, ej. `potencia_ac` en el esquema del Paso 14).

## 8. Trazabilidad de scripts por fase

| Fase                             | Pasos | Scripts principales                                                                                                |
| -------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------ |
| Fase 1 — Datos ambientales       | 4-6   | `datos_nasa_power.py`, `procesar_datos_crudos.py`, `generar_variabilidad_nubosidad.py`                             |
| Fase 2 — Modelo del panel        | 7-10  | `modelo_diodo_unico.py`, `curva_caracteristica.py`, `validacion_modelo_stc.py`, `aplicar_modelo_serie_temporal.py` |
| Fase 3 — MPPT                    | 11-13 | `mppt_perturbar_observar.py`, `simular_seguimiento_mppt.py`, `comparar_ideal_vs_mppt.py`                           |
| Fase 4 — Empaquetado             | 14-15 | `esquema_datos_planta.md`, `interfaz_estado_actual.py`                                                             |
| Fase 5 — Pruebas y documentación | 16-18 | `test_modelo_diodo.py`, `test_pipeline_integracion.py`, `graficar_resultados.py`, este documento                   |

Todas las rutas son relativas a la raíz del repositorio
`tesis-honeypot-fv-ml/`.