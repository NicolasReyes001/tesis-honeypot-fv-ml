# simulacion_fv/ — Módulo de simulación de planta fotovoltaica

Este módulo genera telemetría continua y físicamente coherente de una planta fotovoltaica simulada. Su propósito dentro del proyecto es dotar al honeypot de credibilidad operativa: cualquier atacante que explore la red del laboratorio verá datos reales de un inversor solar en operación activa, no valores fijos o aleatorios.

---

## Estructura

```
simulacion_fv/
├── inversor_modbus/        # Modelo eléctrico del inversor + servidor Modbus
├── mqtt_gateway/           # Publicador MQTT de telemetría FV
├── datasets_irradiancia/   # Datos históricos de irradiancia solar (NASA POWER)
└── pruebas/                # Scripts de validación física del modelo
```

---

## Modelo físico

La simulación se basa en el **modelo de un diodo** del generador fotovoltaico, que describe la relación corriente-voltaje de un panel solar en función de la irradiancia incidente y la temperatura de operación.

### Planta simulada

| Parámetro         | Valor                                            |
| ----------------- | ------------------------------------------------ |
| Tipo              | Inversor solar de cadena                         |
| Potencia nominal  | 5 kW                                             |
| Número de strings | 4 cadenas de paneles en serie                    |
| Referencia        | Parámetros equivalentes a inversor SMA Sunny Boy |

### Variables generadas (cada 5 segundos)

| Variable          | Unidad | Descripción                                              |
| ----------------- | ------ | -------------------------------------------------------- |
| `v_dc`            | V      | Voltaje de corriente continua en la entrada del inversor |
| `i_dc`            | A      | Corriente de corriente continua                          |
| `p_ac`            | W      | Potencia de CA generada a la salida del inversor         |
| `irradiancia`     | W/m²   | Irradiancia solar incidente en el plano del panel        |
| `temp_panel`      | °C     | Temperatura de operación de los paneles                  |
| `estado_inversor` | enum   | Estado operativo: ONLINE / FAULT / OFFLINE               |
| `energia_diaria`  | kWh    | Energía acumulada desde las 00:00 del día actual         |

### Fuente de datos de irradiancia

Los valores de irradiancia se obtienen de la **API NASA POWER** con datos históricos correspondientes a la ciudad de **Santa Marta, Colombia** (latitud 11.24°N, longitud 74.21°W). Esto garantiza que los valores simulados sean representativos de las condiciones reales de operación en la región y no valores genéricos.

---

## Protocolos de publicación

### MQTT (`mqtt_gateway/`)
La telemetría se publica cada 5 segundos en el broker Mosquitto del honeypot bajo el tópico:

```
solar/inversor1/telemetry
```

Formato del payload (JSON):
```json
{
  "timestamp": "2025-06-15T10:30:00",
  "v_dc": 342.5,
  "i_dc": 14.6,
  "p_ac": 4820.0,
  "irradiancia": 980.0,
  "temp_panel": 52.3,
  "estado_inversor": "ONLINE",
  "energia_diaria": 18.4
}
```

### Modbus TCP (`inversor_modbus/`)
Las mismas variables se exponen a través del servidor Modbus TCP señuelo en registros holding mapeados conforme a las especificaciones de equipos de referencia del sector:

| Registro    | Variable          | Escala                       |
| ----------- | ----------------- | ---------------------------- |
| 30001       | `v_dc`            | × 10 (entero sin signo)      |
| 30002       | `i_dc`            | × 100 (entero sin signo)     |
| 30003       | `p_ac`            | × 1 (entero sin signo, W)    |
| 30004       | `irradiancia`     | × 1 (entero sin signo, W/m²) |
| 30005       | `temp_panel`      | × 10 (entero con signo)      |
| 30006       | `estado_inversor` | 1=ONLINE, 2=FAULT, 0=OFFLINE |
| 30007–30008 | `energia_diaria`  | × 100 (entero 32 bits, Wh)   |

---

## Importancia para el honeypot

La simulación cumple dos funciones críticas para el proyecto:

1. **Credibilidad del señuelo:** Un atacante que explora el servidor Modbus verá valores de voltaje, corriente y potencia que varían de forma coherente con la hora del día y las condiciones de irradiancia. Esto aumenta la probabilidad de interacción profunda (lectura de registros, intentos de escritura, manipulación de tópicos MQTT).

2. **Base para detección de FDIA:** Los valores físicamente coherentes del simulador sirven como referencia de comportamiento normal. Las desviaciones significativas respecto a este perfil (por ejemplo, una potencia de 4800 W reportada a medianoche) constituyen la firma característica de un ataque de inyección de datos falsos (Clase 6 del dataset).

---

## Validación del modelo

Los scripts en `pruebas/` verifican que los valores generados cumplan las restricciones físicas del modelo:
- La potencia no puede superar la potencia nominal en condiciones de irradiancia estándar (1000 W/m², 25°C).
- La corriente DC cae a cero cuando `estado_inversor = OFFLINE`.
- La energía diaria acumulada es monótonamente creciente durante horas de luz solar.

---

## Ejecución

```bash
# Instalar dependencias
pip install pymodbus paho-mqtt requests numpy

# Iniciar simulación (publica en MQTT y Modbus cada 5 s)
python simulacion_fv/inversor_modbus/simulador.py

# Ejecutar solo el publicador MQTT
python simulacion_fv/mqtt_gateway/publicador.py

# Descargar datos de irradiancia para Santa Marta
python simulacion_fv/datasets_irradiancia/descargar_nasa_power.py
```