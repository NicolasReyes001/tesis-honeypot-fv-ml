# Comparación de Modelos de Machine Learning para IDS Industriales y Selección del Clasificador del Proyecto
**Semana 2 — Día 5**

## 1. Introducción

El Día 4 de esta semana identificó a Random Forest como el algoritmo más prometedor para el clasificador del proyecto, con base en su frecuencia de uso en la literatura especializada en honeypots y datasets Modbus. Sin embargo, una decisión metodológica de esta naturaleza no puede sustentarse únicamente en la popularidad de un algoritmo dentro de un campo de investigación. El presente documento profundiza esa comparación incorporando criterios técnicos objetivos —métricas de evaluación, comportamiento esperado frente al overfitting, escalabilidad e interpretabilidad— y contrasta dichos criterios contra evidencia cuantitativa reportada en los trabajos ya identificados durante el Día 1 del estado del arte, con el fin de cerrar formalmente la selección del clasificador principal que será implementado y validado experimentalmente durante la Semana 7.

## 2. Métricas de evaluación en Machine Learning

Antes de comparar algoritmos es necesario establecer con qué criterios se medirá su desempeño. La exactitud (accuracy) mide el porcentaje total de predicciones correctas sobre el total de predicciones realizadas; su principal ventaja es la facilidad de interpretación, pero resulta una métrica engañosa cuando las clases están desbalanceadas, un riesgo real para el proyecto dado que se espera que las clases de Replay y FDIA cuenten con muchas menos muestras capturadas experimentalmente que la clase de tráfico normal o escaneo. La precisión (precision) mide qué proporción de las predicciones positivas del modelo fueron realmente correctas, y resulta especialmente relevante cuando los falsos positivos tienen un costo operativo alto, como sería el caso de generar alertas innecesarias sobre la planta fotovoltaica simulada. El recall mide cuántos de los ataques reales presentes en el conjunto de prueba fueron efectivamente detectados por el modelo, siendo crítico cuando no se desea dejar pasar ataques reales sin detectar. El F1-score combina precisión y recall en una sola métrica mediante su media armónica, y constituye una de las métricas más utilizadas en la literatura de IDS precisamente porque equilibra ambos errores, motivo por el cual será adoptada como métrica de referencia principal para evaluar el clasificador del proyecto durante la Semana 7.

## 3. El problema del overfitting

El overfitting ocurre cuando un modelo aprende excesivamente los detalles específicos del conjunto de entrenamiento, incluyendo su ruido particular, en lugar de aprender patrones generalizables. Un síntoma característico es una exactitud muy alta sobre los datos de entrenamiento (por ejemplo, 99%) acompañada de una exactitud sustancialmente menor sobre datos de prueba no vistos (por ejemplo, 65%), lo cual se traduce en mala generalización, detección poco confiable ante nuevos eventos y resultados que no son reproducibles de forma consistente.

Este riesgo es particularmente relevante para el proyecto porque, durante las primeras fases de operación del honeypot, el dataset será relativamente pequeño y probablemente desbalanceado entre clases, condiciones bajo las cuales algunos algoritmos son más propensos al sobreajuste que otros. Esta consideración debe pesar tanto como el desempeño reportado en la literatura al momento de seleccionar el clasificador principal.

## 4. Comparación técnica de los cuatro algoritmos

### Random Forest

Random Forest exhibe típicamente exactitud, precisión y recall altos, con un F1-score consistentemente bueno sobre datos tabulares. Su riesgo de overfitting es moderado-bajo: si bien un árbol de decisión individual es propenso a sobreajustarse, la combinación de múltiples árboles entrenados sobre subconjuntos aleatorios de datos y variables reduce significativamente este riesgo respecto a un árbol único, lo cual es relevante para un dataset inicialmente pequeño como el que tendrá el proyecto en sus primeras semanas de captura. Su interpretabilidad es alta, permitiendo calcular la importancia relativa de cada variable y la contribución de cada atributo a la decisión final, una capacidad valiosa para el capítulo de resultados de la tesis. Su escalabilidad es muy buena, pudiendo procesar miles de registros sin degradación significativa de desempeño.

### Support Vector Machine (SVM)

SVM exhibe típicamente exactitud alta y buen F1-score, con un riesgo de overfitting bajo gracias al principio de maximización del margen entre clases. Su interpretabilidad es limitada: a diferencia de Random Forest, resulta difícil explicar por qué el modelo tomó una decisión específica para un registro dado, lo cual dificulta justificar académicamente los resultados ante un jurado. Su escalabilidad es media, ya que el costo computacional de entrenamiento crece rápidamente a medida que aumenta el tamaño del dataset, una limitación que se vuelve más relevante a medida que el honeypot acumule más eventos capturados a lo largo de las semanas del proyecto.

### K-Nearest Neighbors (KNN)

KNN ofrece buen desempeño en datasets pequeños, pero presenta un riesgo de overfitting alto cuando el parámetro K se configura con un valor pequeño, ya que el modelo se vuelve excesivamente sensible a casos particulares cercanos. Su interpretabilidad es media y su escalabilidad es baja, dado que cada predicción requiere calcular la distancia contra todo el conjunto de datos histórico, lo cual lo hace poco adecuado para una clasificación que deba operar de forma continua sobre un flujo creciente de eventos capturados por el honeypot.

### Isolation Forest

Isolation Forest ofrece un desempeño excelente específicamente para la detección de anomalías, con un riesgo de overfitting muy bajo y una escalabilidad alta. Su limitación crítica para el rol de clasificador principal es que no distingue tipos específicos de ataque: únicamente responde si un registro es normal o anómalo, sin poder etiquetarlo como MITM, FDIA o Replay. Esta limitación lo descarta como clasificador principal del proyecto, pero no invalida su utilidad como herramienta complementaria.

## 5. Tabla comparativa

| Criterio | Random Forest | SVM | KNN | Isolation Forest |
|---|---|---|---|---|
| Accuracy | Alta | Alta | Media | Alta (anomalías) |
| Precision | Alta | Alta | Media | Media |
| Recall | Alto | Alto | Medio | Alto |
| F1-Score | Alto | Alto | Medio | Medio |
| Overfitting | Medio-bajo | Bajo | Alto | Bajo |
| Escalabilidad | Alta | Media | Baja | Alta |
| Interpretabilidad | Alta | Baja | Media | Media |
| Multiclase | Excelente | Buena | Buena | No |
| Datos tabulares | Excelente | Buena | Buena | Buena |
| IDS industrial | Excelente | Buena | Limitada | Complementaria |

## 6. Evidencia cuantitativa en la literatura

Más allá de la comparación cualitativa, es posible contrastar el desempeño esperado de Random Forest contra cifras reales reportadas en los trabajos identificados durante el Día 1 del estado del arte, lo cual aporta una base empírica directa y no solo una tendencia de uso.

Radoglou-Grammatikis et al. (2020), en su sistema de detección de ataques DoS sobre Modbus/TCP evaluado con datos reales provenientes de una planta hidroeléctrica en Grecia, reportan que de los clasificadores evaluados, Random Forest y Adaboost ofrecieron los resultados más eficientes, alcanzando una exactitud del 81% y un F1-score del 77% sobre el conjunto de prueba. Si bien estas cifras no alcanzan el umbral del 90% establecido como criterio de éxito del presente proyecto, constituyen una referencia realista de lo que puede esperarse con un dataset construido sobre tráfico Modbus real y relativamente limitado, en lugar de una cifra optimista de laboratorio. Esta evidencia es valiosa metodológicamente porque permite calibrar expectativas: alcanzar el 90% de F1-score definido en las hipótesis del proyecto será exigente y dependerá fuertemente de la calidad y balance del dataset que se logre construir durante la Semana 7.

El dataset Cyber-Security Modbus ICS, desarrollado por Frazão et al. (2018) y empleado como base de comparación en estudios posteriores de clasificación de tráfico Modbus, resulta particularmente relevante para el proyecto porque incluye explícitamente, entre sus escenarios de captura, una carpeta dedicada a un ataque Man-in-the-Middle basado en ARP spoofing, exactamente el mecanismo de ataque estudiado en profundidad durante el Día 3 de esta semana. Esta coincidencia confirma que el escenario de captura definido por el proyecto no es una construcción artificial, sino que reproduce condiciones de prueba ya validadas y documentadas en la literatura especializada en seguridad de Modbus.

Estudios comparativos adicionales sobre clasificación de tráfico Modbus/TCP confirman que, dentro del conjunto de algoritmos de Machine Learning clásicos (sin incluir arquitecturas de aprendizaje profundo), el árbol de decisión y los ensambles basados en árboles tienden a superar a métodos como Adaboost en escenarios de clasificación binaria sobre datos de intrusión, lo cual refuerza la idoneidad de la familia de algoritmos basados en árboles —de la cual Random Forest es la variante de ensamble más robusta— para el tipo de datos tabulares que generará el honeypot del proyecto.

## 7. Relación con el dataset del proyecto

El dataset que se construirá a partir de los logs del honeypot tendrá cuatro características que coinciden directamente con el escenario donde Random Forest reporta mejor desempeño relativo: será tabular (cada sesión capturada se representa como un vector de atributos), estará etiquetado (cada sesión se clasificará manualmente según el tipo de evento), será multiclase (siete categorías de eventos, según lo definido en días anteriores) y contendrá datos heterogéneos (variables numéricas como `frecuencia_escrituras` o `delta_timestamp_secuencia`, junto con variables binarias como `repeticion_payload` o `cambios_fuera_horario`). Esta combinación de características es precisamente el escenario en el que la literatura revisada reporta el desempeño más consistente de Random Forest frente a SVM y KNN.

## 8. Selección definitiva del clasificador

Con base en la comparación técnica y la evidencia cuantitativa revisada, se establece la siguiente selección metodológica para el proyecto:

**Clasificador principal: Random Forest.** Será el algoritmo implementado y evaluado como núcleo del sistema de detección de intrusiones durante la Semana 7, dado que combina el mejor balance entre exactitud, interpretabilidad, escalabilidad y tolerancia al overfitting frente a un dataset inicialmente pequeño y multiclase.

**Clasificador secundario de referencia: SVM.** Será entrenado sobre el mismo dataset con fines exclusivamente comparativos, permitiendo contrastar sus métricas de desempeño contra las de Random Forest en el capítulo de resultados y fundamentar empíricamente, y no solo teóricamente, la elección del clasificador principal.

**Detector complementario: Isolation Forest.** Podrá emplearse en una etapa posterior del proyecto como mecanismo de validación cruzada o como herramienta exploratoria para identificar posibles anomalías no contempladas explícitamente en las siete clases definidas, particularmente útil si las clases de Replay y FDIA resultan insuficientemente representadas en el dataset capturado experimentalmente, problema ya anticipado en el documento de alcance del sistema de la Semana 1.

## 9. Conclusión metodológica

La comparación técnica realizada en este documento confirma, con una base más rigurosa que la simple frecuencia de uso en la literatura, que Random Forest constituye la opción más adecuada como clasificador principal del proyecto. Esta conclusión se sustenta en tres pilares convergentes: la naturaleza del dataset esperado (tabular, etiquetado, multiclase, heterogéneo) coincide exactamente con el escenario donde Random Forest reporta mejor desempeño relativo frente a SVM y KNN; su tolerancia moderada al overfitting lo hace más robusto que KNN ante el riesgo real de contar con un dataset pequeño durante las primeras fases del proyecto; y la evidencia cuantitativa de trabajos previos sobre Modbus, aunque con cifras que no alcanzan el 90% propuesto como meta del proyecto, confirma que Random Forest se mantiene como el algoritmo de referencia en este dominio específico de aplicación.

Queda como pregunta abierta, a resolver experimentalmente durante la Semana 7, qué tan bien podrá Random Forest distinguir específicamente entre MITM, FDIA, Replay y comportamiento normal utilizando únicamente la evidencia capturada por el honeypot fotovoltaico del proyecto, dado que estas clases no fueron evaluadas de forma diferenciada en los trabajos de referencia citados, los cuales se concentraron principalmente en la detección binaria o en ataques de denegación de servicio.

## Referencias

- Radoglou-Grammatikis, P., Siniosoglou, I., Liatifis, T., Kourouniadis, A., Rompolos, K., & Sarigiannidis, P. (2020). Implementation and Detection of Modbus Cyberattacks. 2020 9th International Conference on Modern Circuits and Systems Technologies (MOCAST), Bremen, Alemania, pp. 1–4. DOI: 10.1109/MOCAST49295.2020.9200287
- Frazão, I., Abreu, P. H., Cruz, T., Araújo, H., & Simões, P. (2018). Denial of Service Attacks: Detecting the Frailties of Machine Learning Algorithms in the Classification Process. 13th International Conference on Critical Information Infrastructures Security (CRITIS 2018), Kaunas, Lituania. Springer Series on Security and Cryptology. DOI: 10.1007/978-3-030-05849-4_19
- Frazão, I., Abreu, P., Cruz, T., Araújo, H., & Simões, P. (2019). Cyber-security Modbus ICS Dataset. IEEE DataPort. DOI: 10.21227/pjff-1a03
- Comparison of the Use of Support Vector Machine (SVM) & Random Forest Algorithms (RF) for DDOS Attack Detection (2025). International Journal of Research and Innovation in Social Science. https://rsisinternational.org/journals/ijriss/articles/comparison-of-the-use-of-support-vector-machine-svm-random-forest-algorithms-rf-for-ddos-attack-detection/
- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. 2008 Eighth IEEE International Conference on Data Mining, pp. 413–422. DOI: 10.1109/ICDM.2008.17
