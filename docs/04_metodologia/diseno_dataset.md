# Diseño del Dataset para la Clasificación de Ataques en el Honeypot Fotovoltaico
**Semana 2 — Día 6**

## 1. Introducción

Durante los días anteriores de esta semana se estableció que los protocolos industriales seleccionados serán Modbus TCP y MQTT, que los ataques de mayor profundidad técnica a estudiar serán MITM, FDIA y Replay, que Random Forest será el clasificador principal del sistema, y que las variables identificadas durante el Día 3 permiten representar comportamiento industrial y no únicamente tráfico de red convencional. Ningún algoritmo de Machine Learning puede funcionar adecuadamente sin un dataset bien diseñado; de hecho, en sistemas de detección de intrusiones la calidad del dataset suele tener mayor impacto sobre el desempeño final que la elección del algoritmo. Por esta razón, antes de iniciar la implementación del honeypot resulta necesario definir formalmente cómo se almacenarán los eventos capturados, qué atributos tendrá cada registro y qué clases serán utilizadas durante el entrenamiento.

Es importante precisar que las clases del dataset definidas en este documento corresponden exactamente a las siete clases establecidas en el alcance del sistema durante la Semana 1 y retomadas en el Día 3 de esta semana, sin introducir categorías adicionales ni eliminar las ya definidas. Esta consistencia es deliberada: mantener una única definición oficial de clases a lo largo de todo el proyecto evita contradicciones entre documentos y facilita la trazabilidad metodológica que un jurado evaluará en la sustentación final.

## 2. ¿Qué es un dataset en Machine Learning?

Un dataset es un conjunto estructurado de observaciones utilizado para entrenar y evaluar modelos de aprendizaje automático. En el contexto del proyecto, cada fila representará un evento o sesión capturada por el honeypot, cada columna representará una característica observable (feature), y una columna adicional contendrá la etiqueta (label) correspondiente a la clase del evento. Un ejemplo simplificado de esta estructura es el siguiente:

| frecuencia_escrituras | repeticion_payload | inconsistencia_fisica | origen_no_habitual | clase                    |
| --------------------- | ------------------ | --------------------- | ------------------ | ------------------------ |
| 3                     | 0                  | 0.02                  | 0                  | Normal                   |
| 25                    | 1                  | 0.01                  | 0                  | Replay Attack            |
| 5                     | 0                  | 0.78                  | 0                  | FDIA                     |
| 4                     | 0                  | 0.05                  | 1                  | Manipulación Modbus/MQTT |

El objetivo del clasificador será aprender la relación existente entre las variables observadas y la etiqueta de salida.

## 3. Definición de las clases del dataset

Considerando el alcance del proyecto establecido desde la Semana 1, se confirman las siguientes siete clases oficiales:

| Clase | Etiqueta                     | Descripción                                                                                                                                                                  |
| ----- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Normal                       | Operación legítima del sistema, sin indicios de actividad maliciosa                                                                                                          |
| 1     | Escaneo                      | Reconocimiento de servicios y puertos expuestos por el honeypot                                                                                                              |
| 2     | Fuerza bruta / Intrusión SSH | Intentos repetidos de autenticación SSH, incluyendo sesiones con acceso exitoso seguido de actividad maliciosa                                                               |
| 3     | Manipulación Modbus/MQTT     | Lectura o escritura no autorizada sobre registros Modbus TCP o manipulación indebida de tópicos MQTT, incluyendo evidencia de ataques MITM ejecutados sobre estos protocolos |
| 4     | DoS/DDoS                     | Inundación de conexiones o solicitudes con el fin de saturar un servicio disponible                                                                                          |
| 5     | Replay Attack                | Reenvío diferido de tramas o mensajes legítimos para forzar acciones no autorizadas                                                                                          |
| 6     | FDIA                         | Modificación maliciosa de variables físicas en registros Modbus o payloads MQTT para inducir decisiones erróneas en el sistema de monitoreo                                  |

Estas clases cubren tres niveles distintos de actividad maliciosa. El primer nivel corresponde al reconocimiento, representado por la clase de Escaneo, que constituye la fase inicial típica de un atacante explorando la red. El segundo nivel corresponde al acceso, representado por la clase de Fuerza bruta/Intrusión SSH, que representa intentos de compromiso directo del sistema mediante el servicio SSH señuelo. El tercer nivel corresponde a la manipulación industrial, integrado por las clases de Manipulación Modbus/MQTT, DoS/DDoS, Replay Attack y FDIA, que representan ataques específicos sobre los protocolos OT e IIoT del proyecto. Esta división por niveles permite construir un IDS con mayor valor académico que un detector binario simple, ya que evidencia una progresión de sofisticación en los comportamientos que el modelo deberá distinguir.

Cabe aclarar específicamente el tratamiento del ataque MITM estudiado en profundidad durante el Día 3 de esta semana: dado que en una red basada en Modbus TCP y MQTT un MITM se manifiesta operativamente como una alteración de las lecturas o escrituras sobre dichos protocolos, su evidencia queda capturada dentro de la clase 3 (Manipulación Modbus/MQTT) en lugar de constituir una clase independiente. Esta decisión, ya adoptada en el documento de alcance del sistema de la Semana 1, se mantiene en el diseño del dataset para preservar la coherencia entre todos los documentos del proyecto.

## 4. Variables del dataset

Las variables deben representar evidencia observable del ataque, organizadas según su origen.

### Variables de red

| Variable           | Tipo                                                               |
| ------------------ | ------------------------------------------------------------------ |
| ip_origen          | Categórica (uso forense, excluida del vector de entrada al modelo) |
| puerto_destino     | Numérica                                                           |
| protocolo          | Categórica                                                         |
| cantidad_paquetes  | Numérica                                                           |
| bytes_transferidos | Numérica                                                           |
| duracion_sesion    | Numérica                                                           |

Estas variables permiten principalmente detectar escaneos y fuerza bruta. Tal como se estableció en el documento de variables de la Semana 1, la dirección IP de origen se conserva en la base de datos con fines forenses, pero se evalúa su exclusión del vector de entrada al modelo para evitar que el clasificador asocie direcciones específicas con comportamiento malicioso en lugar de aprender patrones generalizables.

### Variables Modbus TCP

| Variable              | Tipo                        |
| --------------------- | --------------------------- |
| codigo_funcion        | Numérica                    |
| direccion_registro    | Numérica                    |
| cantidad_registros    | Numérica                    |
| frecuencia_lecturas   | Numérica                    |
| frecuencia_escrituras | Numérica                    |
| tipo_operacion        | Binaria (lectura/escritura) |

Estas variables permiten caracterizar el comportamiento industrial sobre el protocolo Modbus TCP.

### Variables MQTT

| Variable               | Tipo                        |
| ---------------------- | --------------------------- |
| topico                 | Categórica                  |
| frecuencia_publicacion | Numérica                    |
| tamano_payload         | Numérica                    |
| tipo_operacion_mqtt    | Binaria (publish/subscribe) |

Estas variables permiten capturar comportamiento anómalo sobre la capa IIoT del sistema.

### Variables físicas de la simulación FV

| Variable          | Tipo     |
| ----------------- | -------- |
| potencia_generada | Numérica |
| irradiancia       | Numérica |
| temperatura_panel | Numérica |
| voltaje_dc        | Numérica |
| corriente_dc      | Numérica |

Estas variables representan el comportamiento físico del sistema fotovoltaico simulado y constituyen uno de los elementos diferenciadores del proyecto, dado que ningún honeypot reportado en la literatura revisada durante el Día 1 incorpora telemetría física simulada como insumo directo del clasificador.

### Variables derivadas para detección de ataques (definidas en el Día 3)

| Variable                  | Clase relacionada                            |
| ------------------------- | -------------------------------------------- |
| inconsistencia_fisica     | FDIA                                         |
| salto_anomalo_variable    | FDIA                                         |
| variacion_improbable      | FDIA                                         |
| discrepancia_lectura      | Manipulación Modbus/MQTT (evidencia de MITM) |
| origen_no_habitual        | Manipulación Modbus/MQTT (evidencia de MITM) |
| cambios_fuera_horario     | Replay Attack                                |
| delta_timestamp_secuencia | Replay Attack                                |
| repeticion_payload        | Replay Attack                                |

## 5. Estructura final del dataset

Cada fila representará una sesión observada por el honeypot. Un ejemplo de registros con la nomenclatura oficial de clases es el siguiente:

| ip_origen    | codigo_funcion | frecuencia_escrituras | inconsistencia_fisica | repeticion_payload | clase                    |
| ------------ | -------------- | --------------------- | --------------------- | ------------------ | ------------------------ |
| 192.168.1.10 | 3              | 2                     | 0.01                  | 0                  | Normal                   |
| 192.168.1.50 | 16             | 28                    | 0.03                  | 1                  | Replay Attack            |
| 192.168.1.60 | 3              | 4                     | 0.75                  | 0                  | FDIA                     |
| 192.168.1.70 | 6              | 3                     | 0.05                  | 0                  | Manipulación Modbus/MQTT |

Esta estructura será almacenada inicialmente en SQLite, conforme a lo definido en la arquitectura del sistema, y exportada a formato CSV para facilitar su procesamiento con Python y scikit-learn durante la fase de entrenamiento del modelo.

## 6. Balance del dataset

Uno de los mayores problemas en sistemas de detección de intrusiones es el desbalance de clases. Un escenario plausible para el proyecto, dado que las clases más sofisticadas son las más difíciles de capturar experimentalmente, sería el siguiente:

| Clase                        | Cantidad estimada |
| ---------------------------- | ----------------- |
| Normal                       | 5000              |
| Escaneo                      | 1500              |
| Fuerza bruta / Intrusión SSH | 800               |
| Manipulación Modbus/MQTT     | 400               |
| DoS/DDoS                     | 250               |
| Replay Attack                | 80                |
| FDIA                         | 60                |

En este escenario el modelo podría aprender a clasificar casi todo como tráfico normal, obteniendo una exactitud aparentemente alta pero un recall deficiente sobre las clases minoritarias, que son precisamente las más críticas desde la perspectiva de seguridad. Por esta razón, conforme a lo ya establecido en los criterios de éxito del Día 3, será necesario generar escenarios controlados, ejecutar ataques manualmente de forma repetida, y complementar las clases de Replay Attack y FDIA con muestras provenientes de datasets públicos de referencia cuando la captura experimental propia resulte insuficiente.

## 7. Estrategia de etiquetado

Cada evento capturado deberá clasificarse manualmente según el procedimiento que generó la sesión, garantizando trazabilidad entre la acción ejecutada y la etiqueta asignada.

Escaneo: generado mediante herramientas como nmap -sV 192.168.1.100 dirigidas contra los puertos expuestos del honeypot. Etiqueta asignada: Escaneo.

Fuerza bruta / Intrusión SSH: generado mediante herramientas como Hydra contra el servicio SSH señuelo (Cowrie), incluyendo tanto sesiones de intentos fallidos como sesiones con autenticación exitosa seguida de comandos de reconocimiento. Etiqueta asignada: Fuerza bruta/Intrusión SSH.

Manipulación Modbus/MQTT: generado mediante lectura o escritura no autorizada de registros Modbus TCP, manipulación de tópicos MQTT, o simulación de un ataque MITM mediante ARP spoofing con herramientas como Ettercap mientras se intercepta y altera el tráfico Modbus en tránsito. Etiqueta asignada: Manipulación Modbus/MQTT.

DoS/DDoS: generado mediante inundación de solicitudes Modbus o conexiones TCP simultáneas dirigidas a saturar el servicio. Etiqueta asignada: DoS/DDoS.

Replay Attack: generado mediante captura previa de un mensaje legítimo (por ejemplo, una escritura Modbus o una publicación MQTT) y su reenvío posterior fuera de su contexto temporal original. Etiqueta asignada: Replay Attack.

FDIA: generado mediante la publicación de un valor falsificado en un tópico MQTT legítimo, por ejemplo fv/inversor/potencia = 500, sin que dicho valor corresponda a la potencia real generada por la simulación en ese instante. Etiqueta asignada: FDIA.

## 8. División entrenamiento-prueba

La literatura revisada durante esta semana recomienda separar los datos en conjuntos diferenciados para evaluar la capacidad real de generalización del modelo y no únicamente su ajuste sobre los datos ya vistos. La distribución propuesta para el proyecto es la siguiente:

| Conjunto      | Porcentaje |
| ------------- | ---------- |
| Entrenamiento | 70%        |
| Validación    | 15%        |
| Prueba        | 15%        |

Esta proporción de entrenamiento coincide con la empleada por Radoglou-Grammatikis et al. (2020) en su evaluación de clasificadores sobre tráfico Modbus/TCP real, lo cual permite además comparar de forma más directa los resultados experimentales del proyecto contra esa referencia de la literatura durante el capítulo de resultados.

## 9. Relación con Random Forest

El dataset diseñado coincide exactamente con las fortalezas de Random Forest identificadas durante los Días 4 y 5 de esta semana: contiene datos tabulares, variables numéricas y binarias combinadas, y corresponde a un problema de clasificación multiclase sobre un dataset etiquetado. Adicionalmente, Random Forest permite calcular la importancia relativa de cada variable en la decisión de clasificación, lo cual será de gran valor para el capítulo de resultados de la tesis. Un ejemplo ilustrativo del tipo de resultado esperado, a validar experimentalmente durante la Semana 7, sería el siguiente:

| Variable              | Importancia estimada |
| --------------------- | -------------------- |
| inconsistencia_fisica | 0.27                 |
| repeticion_payload    | 0.21                 |
| frecuencia_escrituras | 0.18                 |
| origen_no_habitual    | 0.15                 |

Este tipo de resultado permitirá justificar empíricamente qué indicadores resultan más relevantes para detectar cada tipo de ataque, fortaleciendo la discusión académica del documento final.

## 10. Relación con los objetivos del proyecto

Este diseño conecta directamente todos los componentes definidos hasta el momento del proyecto: el honeypot genera eventos, los logs almacenan dicha información de forma estructurada, el dataset transforma esos eventos en variables interpretables por un algoritmo de Machine Learning, Random Forest aprende los patrones que distinguen cada clase, y el resultado es un IDS inteligente capaz de clasificar automáticamente los ataques industriales capturados. De esta forma, el dataset diseñado en este documento se convierte en el puente metodológico entre la infraestructura señuelo construida durante las semanas siguientes y el sistema de detección basado en Machine Learning que se evaluará formalmente durante la Semana 7.

## 11. Conclusión metodológica

El diseño del dataset realizado en este documento establece la estructura fundamental sobre la cual se construirá el clasificador del proyecto, manteniendo consistencia absoluta con las siete clases oficiales definidas desde la Semana 1 y confirmadas en el Día 3 de esta semana: Normal, Escaneo, Fuerza bruta/Intrusión SSH, Manipulación Modbus/MQTT (que incorpora la evidencia de ataques MITM), DoS/DDoS, Replay Attack y FDIA. Las variables seleccionadas incorporan simultáneamente evidencia de red, comportamiento de protocolo industrial y coherencia física del proceso fotovoltaico simulado, lo cual constituye uno de los elementos diferenciadores del proyecto frente a los honeypots genéricos identificados durante la revisión del estado del arte, ya que el modelo no dependerá únicamente de patrones de tráfico, sino también de información derivada del comportamiento energético simulado.

Asimismo, el análisis confirma que la estructura propuesta es totalmente compatible con el algoritmo Random Forest seleccionado durante los Días 4 y 5, cerrando así la fase de fundamentación metodológica de Machine Learning de la Semana 2 e iniciando la transición hacia la etapa de diseño e implementación del honeypot que se desarrollará durante la Semana 3.


## Resolución temporal de la simulación fotovoltaica

### Ventana temporal

- **Periodo inicial de validación**: 21 de marzo de 2023 (un día completo)
- **Justificación**: Día cercano al equinoccio, con duración solar balanceada (~12h en Bogotá, latitud 4.6°N). Permite validar el modelo sin sesgos estacionales extremos.
- **Escalamiento futuro**: Una vez validado el pipeline, se extenderá a un año completo (ej. 2023-01-01 a 2023-12-31) para la fase de machine learning.

### Resolución temporal

- **Resolución elegida**: 5 minutos (288 puntos por día)
- **Justificación**:
  - Balance entre realismo y volumen de datos manejable.
  - Suficiente para capturar la dinámica de nubosidad (los cambios de irradiancia por nubes típicamente ocurren en escalas de 1-10 minutos).
  - Permite ejecutar el modelo del diodo único 288 veces por día en segundos, facilitando iteraciones rápidas durante la validación.
- **Alternativa considerada**: 1 minuto (1440 puntos/día), descartada por generar 5× más datos sin ganancia significativa en realismo para esta etapa.

### Implicaciones para el dataset

| Escala | Puntos totales | Uso |
|---|---|---|
| 1 día (5 min) | 288 | Validación del modelo, pruebas unitarias, gráficas de tesis |
| 1 mes (5 min) | ~8,640 | Análisis de patrones mensuales |
| 1 año (5 min) | ~105,120 | Entrenamiento de modelos ML, análisis estacional |

### Coordenadas geográficas de referencia

- **Ubicación**: Bogotá, Colombia
- **Latitud**: 4.6097° N
- **Longitud**: 74.0817° W
- **Altitud**: ~2,650 m s.n.m.

> **Nota**: Estas coordenadas se usarán en la Fase 1 (Paso 4) para consultar la API de NASA POWER.