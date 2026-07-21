# Eficiencia de seguimiento del MPPT (Perturbar y Observar)
**Paso 13 — Fase 3, Algoritmo MPPT**

Fecha de ejecución: 2026-07-21 18:44:20

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
  ±5 % de la potencia ideal correspondiente.

## 3. Resultados — comparación de tamaño de paso (paso_V)

| Configuración | Eficiencia de captura de energía | % tiempo dentro de ±5% | Energía ideal (kWh) | Energía MPPT (kWh) |
|---|---|---|---|---|
| paso_pequeño (0.1 V) | 91.64 % | 42.6 % | 0.8742 | 0.8011 |
| paso_grande (2.0 V) | 96.44 % | 78.7 % | 0.8742 | 0.8431 |

## 4. Discusión del compromiso paso pequeño vs. paso grande

En este periodo simulado, el paso grande capturó más energía (96.44 % vs. 91.64 %). Esto puede ocurrir cuando la irradiancia cambia con suficiente rapidez dentro del periodo simulado: un paso grande converge más rápido tras cada cambio, mientras que uno pequeño puede quedarse temporalmente rezagado del nuevo MPP.

Esto ilustra el compromiso clásico del algoritmo P&O documentado en
la literatura (Femia et al., 2005; Esram & Chapman, 2007):

- **Paso pequeño** (paso_pequeño (0.1 V)): mayor precisión en estado
  estacionario (menor oscilación alrededor del MPP real), pero
  converge más lento tras un cambio brusco de irradiancia (ej. el
  paso de una nube), quedándose temporalmente más lejos del MPP
  mientras se re-ajusta.
- **Paso grande** (paso_grande (2.0 V)): converge más rápido tras un cambio
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
