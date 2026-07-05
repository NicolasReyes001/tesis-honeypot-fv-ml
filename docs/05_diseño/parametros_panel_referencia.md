# Parámetros del panel fotovoltaico de referencia

## Panel seleccionado

**Modelo**: Kyocera KC200GT  
**Fabricante**: Kyocera Solar Inc.  
**Tecnología**: Policristalino  
**Potencia nominal (Pmax)**: 200 Wp  
**Fuente**: Datasheet oficial [@kyocera2010kc200gt]

## Condiciones de prueba estándar (STC)

- Irradiancia: 1000 W/m²
- Temperatura de celda: 25 °C
- Masa de aire: AM 1.5

## Parámetros eléctricos extraídos

| Parámetro                     | Símbolo        | Valor   | Unidad |
| ----------------------------- | -------------- | ------- | ------ |
| Potencia máxima               | $P_{max}$      | 200     | W      |
| Voltaje de circuito abierto   | $V_{oc}$       | 32.9    | V      |
| Corriente de cortocircuito    | $I_{sc}$       | 8.21    | A      |
| Voltaje en MPP                | $V_{mpp}$      | 26.3    | V      |
| Corriente en MPP              | $I_{mpp}$      | 7.61    | A      |
| Coef. temperatura de $V_{oc}$ | $\beta_{Voc}$  | −0.126  | V/°C   |
| Coef. temperatura de $I_{sc}$ | $\alpha_{Isc}$ | +0.0026 | A/°C   |
| Número de celdas en serie     | $N_s$          | 72      | —      |

## Parámetros derivados (para el modelo de diodo único)

Estos valores se usarán directamente en `simulacion_fv/planta/parametros_panel.yaml`:

- Voltaje térmico a 25 °C: $V_t = \frac{k \cdot T}{q} \approx 0.02585$ V
- Factor de idealidad inicial estimado: $n \approx 1.2$ (se ajustará en la Fase 2, Paso 9)
- Resistencia serie inicial estimada: $R_s \approx 0.221\ \Omega$ (se ajustará)
- Resistencia shunt inicial estimada: $R_{sh} \approx 415.4\ \Omega$ (se ajustará)

> **Nota**: los valores de $n$, $R_s$ y $R_{sh}$ son estimaciones iniciales basadas en la literatura (Villalva et al., 2009). Serán refinados numéricamente en la Fase 2, Paso 9, hasta que el modelo reproduzca los valores del datasheet con error < 2 %.

## Justificación de la elección

El KC200GT fue seleccionado por ser el panel más utilizado en la literatura académica sobre modelado de diodo único, lo que permite:

1. Comparar directamente los resultados del modelo contra valores publicados.
2. Disponer de un datasheet público y consistente.
3. Usar una configuración de 72 celdas, representativa de paneles comerciales estándar.