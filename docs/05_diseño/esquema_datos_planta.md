# Esquema de datos de salida de la planta fotovoltaica simulada
**Paso 14 — Fase 4, Empaquetar el resultado para consumo futuro**

## 1. Objetivo

Definir el "contrato" estable de variables que la simulación
fotovoltaica expone hacia todo lo que se construya después: el
honeypot (registros Modbus, tópicos MQTT), el dashboard y el
pipeline de Machine Learning. Este esquema **no debe cambiar** una
vez que otros componentes empiecen a consumirlo — si el panel de
referencia o el modelo cambian, solo cambian los valores, no los
nombres ni las unidades de las variables.

## 2. Variables del esquema

| Variable | Tipo | Unidad | Descripción |
|---|---|---|---|
| `timestamp` | string (ISO 8601) | — | Instante de la medición, ej. `2026-03-01T11:35:00` |
| `potencia_dc` | float | W | Potencia DC entregada por el panel/string en este instante |
| `voltaje_dc` | float | V | Voltaje de operación DC (el que decide el MPPT) |
| `corriente_dc` | float | A | Corriente DC de operación (`potencia_dc / voltaje_dc`) |
| `temperatura_panel` | float | °C | Temperatura de la celda/panel |
| `irradiancia` | float | W/m² | Irradiancia global horizontal incidente |

Estas seis variables son exactamente las que un inversor comercial
real expone en su interfaz de monitoreo/Modbus (ej. registros de
potencia, voltaje y corriente DC de entrada, más las variables
ambientales que muchos inversores también reportan desde sus propios
sensores). Mantener el esquema limitado a esto —en vez de incluir
también campos internos de la simulación— es intencional: así el
"contrato" es el mismo que tendría un inversor real, y el día que se
conecte hardware real no hay que rediseñar nada aguas abajo.

## 3. Origen de cada variable (mapeo interno)

La función `obtener_estado_actual()` (Paso 15) traduce las columnas
internas de `datos/processed/potencia_mppt.csv` (Fase 3, Paso 12) a
este esquema:

| Variable del esquema | Columna interna origen |
|---|---|
| `timestamp` | índice del DataFrame (`timestamp`) |
| `potencia_dc` | `P_mppt_w` |
| `voltaje_dc` | `V_mppt` |
| `corriente_dc` | `P_mppt_w / V_mppt` (calculado; 0 si `V_mppt == 0`) |
| `temperatura_panel` | `temperatura_c` |
| `irradiancia` | `irradiancia_wm2` |

**Decisión de diseño importante**: se expone la potencia **seguida
por el MPPT** (`P_mppt_w`, Fase 3), no la potencia "ideal"
(`Pmpp_ideal_w`, Fase 2). Un inversor real nunca entrega la potencia
ideal perfecta — entrega lo que su algoritmo de seguimiento logra
capturar en cada ciclo, con su propio retraso y oscilación. Exponer
la serie ideal haría que el honeypot/dashboard mostraran una planta
"perfecta" que no es representativa de ningún inversor real, lo cual
sería tanto menos realista de cara a un atacante como menos útil
como caso de estudio para la tesis.

`Pmpp_ideal_w` sigue existiendo en `datos/processed/potencia_ideal.csv`
como dato de referencia/diagnóstico interno (para los reportes de
eficiencia del Paso 13), pero no forma parte de este esquema externo.

## 4. Ejemplo de instancia

```json
{
  "timestamp": "2026-03-01T11:35:00",
  "potencia_dc": 149.82,
  "voltaje_dc": 25.74,
  "corriente_dc": 5.822,
  "temperatura_panel": 24.31,
  "irradiancia": 743.2
}
```

## 5. Estabilidad y versionado

- Si en el futuro se necesita una variable adicional (ej. `potencia_ac`
  cuando se modele la eficiencia del inversor DC→AC), se **agrega** al
  esquema sin romper las existentes — nunca se renombran ni se
  eliminan variables ya publicadas.
- Cualquier cambio de unidades (ej. pasar `irradiancia` de W/m² a
  otra escala) requeriría actualizar este documento explícitamente y
  se trataría como un cambio de versión del esquema.

## 6. Uso previsto en fases futuras (fuera del alcance actual)

- `simulacion_fv/modbus/`: cada variable de este esquema se mapea a
  un registro Modbus (holding register), típicamente como entero
  escalado (ej. `potencia_dc * 10` para conservar un decimal en un
  registro de 16 bits).
- `simulacion_fv/mqtt/`: cada variable se publica como un campo del
  payload JSON de un tópico único, o como tópicos separados por
  variable, replicando el patrón de un gateway de planta solar real.