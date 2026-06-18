# Machine Learning para IDS Industriales
**Semana 2 — Día 4**

## 1. Introducción

Los días anteriores de esta semana permitieron establecer que existe evidencia científica e industrial sólida sobre la presencia de honeypots aplicados a entornos SCADA, que la infraestructura solar fotovoltaica constituye un objetivo real de ciberataques documentados, y que ataques como MITM, FDIA y Replay dejan huellas técnicas distinguibles sobre los protocolos Modbus TCP y MQTT. El presente documento cierra este ciclo de fundamentación al abordar la pregunta de cómo dichas huellas pueden traducirse en una clasificación automática mediante Machine Learning, estableciendo la base técnica que sustentará la selección del algoritmo clasificador del proyecto.

A diferencia de los sistemas de detección de intrusiones tradicionales, que dependen de reglas estáticas o firmas conocidas, un IDS basado en Machine Learning aprende patrones de comportamiento normal y anómalo directamente de los datos históricos, lo que resulta particularmente relevante para un honeypot orientado a un dominio específico como la generación fotovoltaica, donde no existen firmas comerciales predefinidas para ataques como FDIA o Replay sobre telemetría solar.

## 2. IDS basados en firmas frente a IDS basados en Machine Learning

Los sistemas de detección de intrusiones tradicionales operan mediante la comparación del tráfico observado contra un conjunto de firmas o reglas predefinidas. Por ejemplo, una regla puede especificar que la ejecución del comando `rm -rf /` debe generar una alerta, o que más de 100 intentos de autenticación SSH en un minuto desde la misma IP constituye un patrón de fuerza bruta. Este enfoque tiene como ventajas su simplicidad de implementación, su velocidad de procesamiento y una tasa relativamente baja de falsos positivos cuando las reglas están bien calibradas. Sus desventajas, sin embargo, son significativas para el contexto del proyecto: no son capaces de detectar ataques nuevos o variantes no contempladas en el conjunto de reglas, requieren actualización manual constante a medida que surgen nuevas amenazas, y resultan particularmente difíciles de adaptar a un dominio de aplicación específico como la generación fotovoltaica, donde no existen catálogos de firmas comerciales para ataques como FDIA sobre irradiancia solar o Replay sobre telemetría MQTT de un inversor.

Un IDS basado en Machine Learning invierte esta lógica: en lugar de buscar coincidencias con firmas conocidas, el modelo aprende automáticamente, a partir de datos históricos etiquetados o no etiquetados, qué patrones corresponden a comportamiento normal y cuáles corresponden a comportamiento anómalo o malicioso. Por ejemplo, si la potencia reportada por un inversor fotovoltaico oscila normalmente entre 98 y 102 kW bajo ciertas condiciones de irradiancia, y de manera súbita se reporta un valor de 450 kW sin una transición gradual coherente, el modelo puede aprender a identificar dicho salto como una anomalía característica de un FDIA, sin que haya sido necesario programar explícitamente una regla para ese caso particular.

## 3. Tipos de aprendizaje aplicables a IDS

El aprendizaje supervisado utiliza un conjunto de datos en el que cada registro está etiquetado con la clase a la que pertenece (normal, Replay, FDIA, MITM, entre otras), permitiendo que el modelo aprenda explícitamente las diferencias estadísticas entre clases. Este es el enfoque que adoptará el presente proyecto, dado que el honeypot generará registros que serán etiquetados manualmente según el tipo de interacción capturada.

El aprendizaje no supervisado, en cambio, no requiere etiquetas: el algoritmo busca identificar registros que se comporten de manera sustancialmente distinta al resto del conjunto de datos, asumiéndolos como anomalías. Este enfoque es particularmente útil cuando no se dispone de suficientes muestras etiquetadas de un tipo de ataque específico, pero tiene la limitación de que, al no existir clases predefinidas, el modelo puede señalar que algo es anómalo sin poder especificar de qué tipo de ataque se trata.

El aprendizaje semi-supervisado combina ambos enfoques, entrenando principalmente con datos de comportamiento normal y señalando como anómalo cualquier registro que se desvíe significativamente del perfil aprendido, sin necesidad de contar con ejemplos etiquetados de cada tipo de ataque posible.

## 4. Algoritmos evaluados

### Random Forest

Random Forest es un algoritmo de aprendizaje supervisado basado en ensambles de múltiples árboles de decisión entrenados sobre subconjuntos aleatorios de los datos y las variables. Cada árbol emite una predicción de clase de forma independiente, y la clase final asignada al registro corresponde a la mayoría de votos entre todos los árboles del ensamble. Entre sus principales ventajas se encuentran una alta precisión de clasificación, robustez frente al ruido en los datos, capacidad de manejar variables heterogéneas (numéricas y categóricas simultáneamente), facilidad relativa de interpretación mediante la importancia de variables, bajo requerimiento de ajuste de hiperparámetros, y un desempeño consistentemente sólido sobre datos tabulares, que es precisamente la naturaleza del dataset que generará el honeypot del proyecto. Múltiples estudios comparativos confirman que Random Forest supera frecuentemente a otros algoritmos como SVM y Naive Bayes en tareas de detección de intrusiones, particularmente en datos provenientes de IoT, y se ha reportado como un componente base efectivo incluso en arquitecturas híbridas más complejas, como combinaciones con redes neuronales convolucionales para extracción de características.

### Support Vector Machine (SVM)

SVM es un algoritmo que busca construir una frontera de decisión matemática que separe las clases del conjunto de datos, maximizando la distancia entre dicha frontera y los puntos más cercanos de cada clase. Sus ventajas incluyen buena precisión de clasificación y robustez matemática, además de un desempeño aceptable incluso con conjuntos de datos relativamente pequeños. Sus desventajas son relevantes para el contexto del proyecto: su tiempo de entrenamiento escala deficientemente con el tamaño del dataset, ofrece menor interpretabilidad que los modelos basados en árboles, y resulta más costoso computacionalmente de entrenar, lo cual es una consideración importante si el entrenamiento se realiza sobre el mismo hardware del honeypot o sobre una máquina de soporte con recursos limitados. En estudios comparativos sobre detección de ataques DDoS, SVM ha mostrado tasas de precisión sustancialmente menores que Random Forest sobre los mismos conjuntos de datos.

### K-Nearest Neighbors (KNN)

KNN clasifica un nuevo registro según la clase predominante entre sus k vecinos más cercanos en el espacio de características. Es sencillo de implementar y no requiere una fase de entrenamiento compleja, pero presenta desventajas significativas para un sistema que podría escalar en volumen de datos: su tiempo de predicción es lento en producción porque debe calcular distancias contra todo el conjunto de entrenamiento, es sensible al ruido en los datos, y consume una cantidad de memoria proporcional al tamaño del dataset histórico almacenado.

### Isolation Forest

A diferencia de los tres algoritmos anteriores, Isolation Forest es un algoritmo de aprendizaje no supervisado diseñado específicamente para la detección de anomalías. Su principio de funcionamiento es opuesto al de la mayoría de técnicas de detección, que construyen un perfil de lo que es "normal": Isolation Forest, en cambio, aísla explícitamente los puntos anómalos del conjunto de datos, partiendo de la premisa de que los registros normales son difíciles de aislar mediante particiones aleatorias del espacio de características, mientras que los registros anómalos se aíslan con muy pocas particiones. Su principal ventaja es que resulta muy útil cuando no existen etiquetas disponibles y puede detectar comportamientos completamente desconocidos; su principal desventaja para el proyecto es que únicamente indica si un registro parece anómalo, sin ser capaz de clasificar a qué tipo específico de ataque corresponde dicha anomalía, lo cual lo descalifica como clasificador principal pero no como herramienta complementaria de validación.

## 5. Tabla comparativa

| Algoritmo | Tipo de aprendizaje | Ventaja principal | Limitación principal | Idoneidad para el proyecto |
|---|---|---|---|---|
| Random Forest | Supervisado | Alta precisión en datos tabulares heterogéneos, interpretable, robusto al ruido | Menor interpretabilidad que un árbol único, aunque mayor que SVM | Alta — coincide exactamente con la naturaleza del dataset (tabular, etiquetado, multiclase) |
| SVM | Supervisado | Buena precisión con datasets pequeños | Escala mal con datasets grandes, costoso de entrenar | Media — viable en fase inicial, limitante si el dataset crece |
| KNN | Supervisado | Simplicidad de implementación | Lento en producción, sensible al ruido, alto consumo de memoria | Baja — poco práctico para clasificación en tiempo casi real |
| Isolation Forest | No supervisado | Detecta anomalías desconocidas sin necesidad de etiquetas | No clasifica el tipo específico de ataque | Complementaria — útil como validación cruzada, no como clasificador principal |

## 6. ¿Qué algoritmo utiliza más la literatura?

La revisión de literatura realizada durante esta semana, particularmente durante el Día 1 dedicado al estado del arte de honeypots industriales, confirma una tendencia consistente hacia el uso de Random Forest como algoritmo predilecto en trabajos que combinan honeypots o capturas de tráfico industrial con clasificación de Machine Learning. Tanto el trabajo de Frazão et al. sobre el dataset Cyber-Security Modbus ICS como el de Radoglou-Grammatikis et al. sobre implementación y detección de ciberataques Modbus emplean Random Forest como parte central de su metodología de evaluación, reportando desempeños consistentes sobre datos tabulares derivados de protocolos OT. Esta convergencia metodológica en la literatura especializada en el dominio específico del proyecto (honeypots + Modbus + ML) constituye una justificación adicional, más allá de la evidencia general de la literatura de IDS, para adoptar Random Forest como algoritmo clasificador principal.

## 7. Relación con las variables del proyecto

Las variables identificadas durante el Día 3 de esta semana, asociadas a los ataques MITM, FDIA y Replay, pueden incorporarse directamente como atributos de entrada del clasificador sin transformación adicional significativa, dado que Random Forest maneja sin dificultad la combinación de variables numéricas y binarias:

| Variable | Tipo | Naturaleza para el modelo |
|---|---|---|
| frecuencia_escrituras | Numérica | Atributo continuo directo |
| repeticion_payload | Binaria | Atributo categórico binario |
| inconsistencia_fisica | Numérica | Atributo continuo directo |
| salto_anomalo_variable | Numérica | Atributo continuo directo |
| variacion_improbable | Numérica | Atributo continuo directo |
| discrepancia_lectura | Numérica | Atributo continuo directo |
| cambios_fuera_horario | Binaria | Atributo categórico binario |
| origen_no_habitual | Binaria | Atributo categórico binario |
| delta_timestamp_secuencia | Numérica | Atributo continuo directo |

Esta compatibilidad directa entre el tipo de variables generadas por el honeypot y los requerimientos de entrada de Random Forest refuerza la coherencia metodológica del proyecto: el diseño de las variables de captura, realizado sin conocer aún el algoritmo final, resulta naturalmente adecuado para el clasificador seleccionado, precisamente porque ambos parten de la misma naturaleza tabular y heterogénea de los datos de red industrial.

## 8. Justificación preliminar de la selección de Random Forest

Con base en el análisis comparativo realizado, Random Forest se selecciona como algoritmo clasificador principal del proyecto por tres razones convergentes. En primer lugar, el dataset que generará el honeypot será tabular, etiquetado y multiclase, exactamente el escenario donde la literatura reporta el mejor desempeño relativo de Random Forest frente a SVM y KNN. En segundo lugar, su capacidad de manejar variables heterogéneas sin normalización compleja se ajusta directamente a la combinación de atributos numéricos y binarios definidos en el Día 3. En tercer lugar, su uso recurrente en los trabajos más cercanos metodológicamente al presente proyecto, identificados durante la revisión del estado del arte, proporciona un respaldo empírico específico al dominio de aplicación, más allá de la evidencia genérica de la literatura de IDS. Esta selección se mantiene como preliminar y será validada experimentalmente durante la Semana 7, mediante comparación directa de métricas de desempeño frente a SVM y árbol de decisión sobre el dataset real construido a partir de las capturas del honeypot.

## 9. Conclusiones

El análisis realizado en este documento confirma que la transición de un IDS basado en reglas hacia un IDS basado en Machine Learning es metodológicamente necesaria para el dominio de aplicación del proyecto, dado que no existen firmas comerciales predefinidas para ataques específicos sobre infraestructura fotovoltaica simulada como FDIA sobre irradiancia o Replay sobre telemetría MQTT de inversores. De los cuatro algoritmos evaluados, Random Forest se posiciona como la opción más adecuada para la fase de clasificación principal, dado que su naturaleza se ajusta directamente al tipo de dataset que el honeypot generará y cuenta con respaldo consistente tanto en la literatura general de IDS como en los trabajos específicos del dominio honeypot-Modbus-ML revisados durante esta semana. Isolation Forest se reconoce como una herramienta complementaria de valor para escenarios donde el etiquetado resulte insuficiente, particularmente para las clases de ataque más difíciles de capturar experimentalmente, como Replay y FDIA, mencionadas en los días anteriores de esta semana.

## Referencias

- Frazão, I., Abreu, P. H., Cruz, T., Araújo, H., & Simões, P. (2018). Denial of Service Attacks: Detecting the Frailties of Machine Learning Algorithms in the Classification Process. 13th International Conference on Critical Information Infrastructures Security (CRITIS 2018), Kaunas, Lituania. DOI: 10.1007/978-3-030-05849-4_19
- Radoglou-Grammatikis, P., Siniosoglou, I., Liatifis, T., Kourouniadis, A., Rompolos, K., & Sarigiannidis, P. (2020). Implementation and Detection of Modbus Cyberattacks. 2020 9th International Conference on Modern Circuits and Systems Technologies (MOCAST), Bremen, Alemania, pp. 1–4. DOI: 10.1109/MOCAST49295.2020.9200287
- Comparison of the Use of Support Vector Machine (SVM) & Random Forest Algorithms (RF) for DDOS Attack Detection (2025). International Journal of Research and Innovation in Social Science. https://rsisinternational.org/journals/ijriss/articles/comparison-of-the-use-of-support-vector-machine-svm-random-forest-algorithms-rf-for-ddos-attack-detection/
- Comparison of Random Forest, K-Nearest Neighbor, and Support Vector Machine Classifiers for Intrusion Detection System (2024). ResearchGate. https://www.researchgate.net/publication/383162577
- Intrusion detection system combined enhanced random forest with SMOTE algorithm (2022). Journal on Advances in Signal Processing, Springer Nature. https://link.springer.com/article/10.1186/s13634-022-00871-6
- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. 2008 Eighth IEEE International Conference on Data Mining, pp. 413–422. DOI: 10.1109/ICDM.2008.17
