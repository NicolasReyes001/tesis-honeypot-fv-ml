# datos/ — Pipeline de datos del proyecto

Esta carpeta contiene los datos en sus distintas etapas de procesamiento: desde los logs crudos capturados por el honeypot hasta el dataset final etiquetado y listo para entrenar el clasificador. La separación por etapas permite reproducir el pipeline desde cualquier punto sin mezclar datos de distintas fases.

---

## Estructura

```
datos/
├── raw/           # Logs y PCAP directamente del honeypot, sin modificar
├── procesados/    # Eventos con features extraídas, en CSV estructurado
├── etiquetados/   # Dataset final con columna de clase asignada
└── externos/      # Datasets públicos de referencia descargados
```

---

## Flujo de datos

```
honeypot/ (logs JSON + PCAP)
        ↓
datos/raw/            ← copias exactas sin modificar, nunca se tocan
        ↓  [parser Python]
datos/procesados/     ← CSV con features extraídas, sin etiqueta
        ↓  [etiquetado manual + scripts]
datos/etiquetados/    ← dataset_final.csv con columna "clase"
        ↓  [ml/preprocessing/]
ml/notebooks/         ← entrenamiento del clasificador
```

---

## `raw/`

Archivos de log en su formato original, tal como los genera cada componente del honeypot. **Nunca se modifican.** Son la fuente de verdad del proyecto.

| Archivo esperado        | Origen                    | Formato            |
| ----------------------- | ------------------------- | ------------------ |
| `cowrie_YYYYMMDD.json`  | Cowrie (SSH)              | JSON Lines         |
| `modbus_YYYYMMDD.log`   | Servidor PyModbus señuelo | JSON Lines         |
| `mqtt_YYYYMMDD.log`     | Mosquitto con logging     | Texto plano / JSON |
| `captura_YYYYMMDD.pcap` | tcpdump                   | PCAP binario       |

---

## `procesados/`

CSV generado por los scripts de parseo en `ml/preprocessing/`. Una fila por evento de red. Incluye todas las features extraídas pero **sin columna de clase** (aún sin etiquetar).

Columnas esperadas: `timestamp`, `ip_origen`, `puerto_destino`, `protocolo`, `duracion_sesion`, `num_intentos_login`, `num_comandos`, `num_registros_modbus`, `tam_payload_bytes`, `num_paquetes`, `tasa_paquetes`, `hora_del_dia`, `credencial_valida`, `usuario_existente`, `credencial_default`, `tipo_op_modbus`, `tipo_op_mqtt`, `inconsistencia_fisica`, `repeticion_payload`.

---

## `etiquetados/`

Dataset final con la columna `clase` añadida. Es el archivo de entrada para el módulo de ML.

| Archivo             | Descripción                                                           |
| ------------------- | --------------------------------------------------------------------- |
| `dataset_final.csv` | Dataset completo con todas las clases (7 clases, ≥500 muestras/clase) |
| `train.csv`         | Conjunto de entrenamiento (70%, estratificado)                        |
| `test.csv`          | Conjunto de prueba independiente (30%, estratificado)                 |

### Clases en el dataset

| Clase | Etiqueta                     | Fuente primaria              |
| ----- | ---------------------------- | ---------------------------- |
| 0     | Normal                       | Captura honeypot             |
| 1     | Escaneo                      | Captura honeypot             |
| 2     | Fuerza bruta / Intrusión SSH | Captura honeypot (Cowrie)    |
| 3     | Manipulación Modbus/MQTT     | Captura honeypot             |
| 4     | DoS/DDoS                     | Captura honeypot             |
| 5     | Replay Attack                | Captura honeypot + UNSW-NB15 |
| 6     | FDIA                         | Captura honeypot + UNSW-NB15 |

---

## `externos/`

Datasets públicos de referencia usados para complementar las clases 5 y 6 si la captura experimental no genera suficientes muestras propias.

| Dataset   | Fuente                         | Uso                         |
| --------- | ------------------------------ | --------------------------- |
| UNSW-NB15 | Universidad de New South Wales | Complemento de clases 5 y 6 |

Los datos externos se descargan con el script `ml/scripts/descargar_datasets.py` y se almacenan aquí sin modificar. La integración con el dataset propio se realiza en el notebook de ingeniería de features.

---

## Notas importantes

- Los datos en `raw/` y `etiquetados/` están incluidos en `.gitignore` si contienen información personal (IPs reales). Si el repositorio es público, deben anonimizarse antes de subir.
- El archivo `test.csv` debe mantenerse completamente separado durante el desarrollo del modelo para evitar data leakage.