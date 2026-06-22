# ml/ — Módulo de machine learning

Este módulo contiene todo el pipeline de aprendizaje automático del proyecto: desde el preprocesamiento del dataset hasta el entrenamiento, evaluación y serialización del clasificador Random Forest. Es el componente que transforma los eventos capturados por el honeypot en alertas clasificadas por tipo de ataque.

---

## Estructura

```
ml/
├── notebooks/       # Notebooks de exploración, análisis y entrenamiento
├── preprocessing/   # Scripts de limpieza e ingeniería de features
├── modelos/         # Modelos entrenados serializados (.pkl, .joblib)
├── evaluacion/      # Métricas, matrices de confusión y curvas ROC
└── scripts/         # Scripts de entrenamiento e inferencia en producción
```

---

## Tarea de clasificación

El clasificador asigna a cada evento capturado por el honeypot una de las siguientes siete clases:

| Clase | Etiqueta                     | Descripción                                                                                   |
| ----- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| 0     | Normal                       | Tráfico legítimo sin indicios de actividad maliciosa                                          |
| 1     | Escaneo                      | Exploración de puertos o descubrimiento de servicios                                          |
| 2     | Fuerza bruta / Intrusión SSH | Intentos repetidos de autenticación SSH y sesiones con actividad maliciosa post-acceso        |
| 3     | Manipulación Modbus/MQTT     | Acceso no autorizado a registros Modbus TCP o tópicos MQTT (incluye evidencia de MITM)        |
| 4     | DoS/DDoS                     | Inundación de conexiones para saturar un servicio disponible                                  |
| 5     | Replay Attack                | Reenvío diferido de tramas legítimas para forzar acciones no autorizadas                      |
| 6     | FDIA                         | Modificación maliciosa de variables físicas en Modbus o MQTT para inducir decisiones erróneas |

Las clases 5 y 6 pueden complementarse con muestras de datasets públicos (UNSW-NB15) si la captura experimental no genera suficientes muestras propias.

---

## Features de entrada al modelo

El vector de características se extrae de los logs del honeypot y de los archivos PCAP capturados por tcpdump:

| Feature                 | Origen                  | Tipo                              |
| ----------------------- | ----------------------- | --------------------------------- |
| `duracion_sesion`       | Red general / Cowrie    | Numérica (s)                      |
| `num_intentos_login`    | Cowrie (SSH)            | Numérica                          |
| `num_comandos`          | Cowrie (SSH)            | Numérica                          |
| `puerto_destino`        | Red general             | Categórica                        |
| `protocolo`             | Red general             | Categórica (SSH/Modbus/MQTT/HTTP) |
| `num_registros_modbus`  | Servidor Modbus señuelo | Numérica                          |
| `tam_payload_bytes`     | MQTT / Red general      | Numérica                          |
| `num_paquetes`          | PCAP (tcpdump)          | Numérica                          |
| `tasa_paquetes`         | PCAP (tcpdump)          | Numérica (pkt/s)                  |
| `hora_del_dia`          | Timestamp del evento    | Numérica (0–23)                   |
| `credencial_valida`     | Cowrie (SSH)            | Binaria (0/1)                     |
| `usuario_existente`     | Cowrie (SSH)            | Binaria (0/1)                     |
| `credencial_default`    | Cowrie (SSH)            | Binaria (0/1)                     |
| `tipo_op_modbus`        | Servidor Modbus         | Binaria (lectura=0, escritura=1)  |
| `tipo_op_mqtt`          | Mosquitto logs          | Binaria (subscribe=0, publish=1)  |
| `inconsistencia_fisica` | Simulación FV           | Numérica (desviación del modelo)  |
| `repeticion_payload`    | Análisis PCAP           | Binaria (0/1)                     |

La dirección IP de origen se almacena en la base de datos con valor forense pero **se excluye del vector de entrada al modelo** para evitar que el clasificador aprenda patrones asociados a IPs específicas en lugar de comportamientos generalizables.

---

## Algoritmo principal

**Random Forest** con 100 árboles de decisión. Justificación:
- Desempeño consistentemente alto sobre datos tabulares heterogéneos.
- Resistencia al overfitting moderada gracias al ensamble de árboles entrenados sobre subconjuntos aleatorios.
- Alta interpretabilidad mediante importancia de variables, útil para la discusión académica de resultados.
- No requiere normalización intensiva de features.
- Múltiples estudios comparativos en IDS industriales reportan que supera a SVM y KNN en datos de este tipo.

**Clasificadores de comparación** (para la discusión de resultados): SVM con kernel RBF y árbol de decisión simple.

---

## Métricas de evaluación

Se reportan las siguientes métricas sobre el conjunto de prueba (30% del dataset, estratificado por clase):

- Accuracy global
- Precision, Recall y F1-score por clase
- Matriz de confusión (7×7)
- Curva ROC y AUC por clase (one-vs-rest)
- Importancia de variables (Gini impurity)

La métrica principal de referencia es el **F1-score macro promediado**, que equilibra precision y recall para todas las clases independientemente de su frecuencia en el dataset.

---

## Dataset de entrenamiento

| Fuente                    | Descripción                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| Logs propios del honeypot | Eventos capturados durante las semanas 1–6 de operación, etiquetados manualmente                      |
| UNSW-NB15 (complemento)   | Dataset público de referencia, usado para completar clases 5 y 6 si la captura propia es insuficiente |

División del dataset: 70% entrenamiento / 30% prueba, con estratificación por clase.

---

## Notebooks

| Archivo                        | Contenido                                                                        |
| ------------------------------ | -------------------------------------------------------------------------------- |
| `01_exploracion_dataset.ipynb` | Análisis exploratorio: distribución de clases, correlaciones, valores nulos      |
| `02_ingenieria_features.ipynb` | Transformaciones, encoding de variables categóricas, normalización               |
| `03_entrenamiento_rf.ipynb`    | Entrenamiento del Random Forest, búsqueda de hiperparámetros, validación cruzada |
| `04_evaluacion.ipynb`          | Métricas, matriz de confusión, curvas ROC, importancia de variables              |
| `05_comparacion_modelos.ipynb` | Comparación Random Forest vs. SVM vs. árbol de decisión                          |

---

## Ejecución

```bash
# Instalar dependencias
pip install scikit-learn pandas numpy matplotlib seaborn joblib imbalanced-learn

# Entrenar el modelo
python ml/scripts/entrenar.py --datos datos/etiquetados/dataset_final.csv

# Evaluar sobre conjunto de prueba
python ml/scripts/evaluar.py --modelo ml/modelos/rf_v1.pkl --prueba datos/etiquetados/test.csv

# Inferencia sobre nuevos eventos
python ml/scripts/inferir.py --evento <json_del_evento>
```