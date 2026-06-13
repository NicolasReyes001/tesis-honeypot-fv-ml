## 1. Introducción.

Los sistemas fotovoltaicos modernos presentan vulnerabilidades de ciberseguridad debido a la ausencia de mecanismos nativos robustos o que se suelen omitir en la práctica, como el cifrado y la autentificación de protocolos de comunicación como Modbus TCP y MQTT. Esta condición se complica debido a las limitaciones metodológicas y regulatorias de ejecutar ataques dirigidos a entornos de producción real; esto genera vacíos críticos de seguridad en datos operativos y firmas de tráfico anómalo para entrenamiento de sistemas de detección.

Ante este escenario, cualquier solución tecnológica debe someterse a procesos de validación objetivos y científicos para que la implementación trascienda de lo simple a lo técnico. Es imperativo poder determinar con gran precisión cuáles son los componentes que serán evaluados y poder definir de manera cualitativa y cuantitativa la evidencia empírica que pueda comprobar la viabilidad y utilidad de la propuesta real, garantizando que el diseño propuesto responda con fidelidad a las problemáticas de los sistemas fotovoltaicos en términos de ciberseguridad.

Por consiguiente, el sistema propuesto se constituye de un honeypot de media interacción en una Raspberry Pi 4, un módulo de simulación físico-matemático que describa una planta fotovoltaica real y un clasificador basado en Machine Learning. Será evaluado a partir de preguntas de investigación e hipótesis de trabajo bien delimitadas. Este enfoque metodológico permitirá auditar tanto la credibilidad del entorno propuesto como señuelo para posibles atacantes, como de tener la capacidad del modelo para poder diferenciar entre tráfico legítimo y malicioso.

Con este propósito, el presente documento define formalmente las preguntas de investigación, las hipótesis de trabajo y la matriz de variables preliminares que orientan el proyecto hacia un desarrollo experimental y a la posterior validación como tesis de grado.

## 2. Preguntas de investigación.

#### Pregunta general.

¿Es posible que un honeypot de media interacción, integrado con simulación fotovoltaica y un clasificador Random Forest, detecte y clasifique ataques dirigidos a sistemas SCADA fotovoltaicos con un F1-score superior al 90%?

#### Preguntas específicas.

¿En qué medida la telemetría generada mediante un modelo físico-matemático mantiene coherencia con el comportamiento esperado de una planta fotovoltaica real cuando es expuesta a través de servicios Modbus TCP y MQTT, y en qué medida dicha coherencia contribuye a la captura de eventos de ciberseguridad relevantes para el análisis de amenazas?

¿Cuál es el nivel de precisión, recall y puntuación F1 del algoritmo Random Forest al clasificar los eventos capturados por el honeypot en las categorías de tráfico predefinidas?

¿Qué características y atributos relevantes para la detección de intrusiones pueden obtenerse mediante un honeypot orientado a servicios utilizados en sistemas fotovoltaicos, como SSH, HTTP, Modbus TCP y MQTT?

Las preguntas formuladas permiten evaluar integralmente los componentes de la propuesta, desde la generación de un entorno fotovoltaico creíble y la captura de eventos relevantes, hasta la capacidad del modelo de aprendizaje automático para apoyar la detección de amenazas en infraestructuras fotovoltaicas basadas en tecnologías SCADA e IIoT.

## 3. Hipótesis.

#### Hipótesis 1.

Si se alimenta la interfaz de los servidores señuelos (Modbus TCP y MQTT) con un modelo dinámico físico-matemático basado en ecuaciones del inversor, como la eficiencia y datos de irradiancia local, entonces las mediciones de lecturas externas de potencia, voltaje y corriente mantendrán una desviación porcentual menor al 5% respecto al comportamiento real de la planta fotovoltaica.

El método consiste en vincular el modelo matemático-solar y los datos históricos a servicios como lo son el Modbus TCP y MQTT, los cuales están expuestos en la Raspberry Pi 4; con esto se espera lograr que la desviación de las variables obtenidas sea menor al 5% y así lograr un entorno señuelo creíble y útil para la captura de ataques cibernéticos.

La justificación radica en que al exponer servicios OT e IoT, los ataques dejan de ser ruido genérico y se transforman en datos estructurados que incluyen marcas de tiempo, credenciales y comandos específicos del sector eléctrico solar.

#### Hipótesis 2.

Si se entrena un algoritmo de machine learning basado en random forest y que este utilice características tabulares que son extraídas del historial de los logs del sistema, el sistema logrará alcanzar una precisión, recall y puntuación F1 superior al 90% al clasificar el tráfico y eventos legítimos y maliciosos definidos para el estudio.

Como método se tiene el entrenamiento del clasificador Random Forest con los datos etiquetados de tráfico normal y malicioso del sistema; con esto se espera un resultado de las métricas de rendimiento que sea superior al 90% sobre el conjunto de prueba independiente.

Como justificación, se tiene que los árboles de decisión del algoritmo manejan de forma excelente las fronteras de los datos tabulares cada vez que un ataque cambia drásticamente los umbrales de la red.

#### Hipótesis 3.

Si el honeypot expone simultáneamente servicios representativos de entornos fotovoltaicos, como SSH, HTTP, Modbus TCP y MQTT, entonces será posible construir un dataset con al menos 500 eventos etiquetados por clase y un porcentaje de registros incompletos inferior al 5% con características suficientes para construir un dataset destinado al entrenamiento de modelos de detección de intrusiones.

El método es desplegar y monitorear de forma centralizada a superficie de ataque multi-servicio (puertos 80, 22, 502 y 1883), con esto se espera obtener un mínimo de 500 eventos etiquetados por clase, con menos del 5% de registros incompletos, suficientes para entrenar el modelo.

La justificación radica en que al exponer servicios específicos de entornos OT e IoT, los ataques dejan de ser intentos genéricos y se transforman en datos estructurados que incluyen marcas de tiempo, credenciales y comandos específicos del sector energético, los cuales son insumo directo para la construcción del dataset.

## 4. Variables del sistema

### Características de entrada del modelo (features).

Las variables independientes constituyen el conjunto de atributos que serán extraídos de cada sesión registrada por el honeypot y que servirán como entrada al modelo de machine learning. Se organizan según el protocolo o capa de red de la que provienen.

#### SSH
Del servicio SSH se extraerán las siguientes variables: número de intentos de autenticación realizados durante la sesión, número de comandos ejecutados una vez establecida la conexión, duración total de la sesión en segundos, y tres variables binarias independientes derivadas del resultado de autenticación. La primera indicará si la credencial utilizada resultó válida o inválida; la segunda, si el nombre de usuario corresponde a un usuario existente en el sistema o no; y la tercera, si la credencial empleada corresponde a una credencial por defecto conocida o a una personalizada. La separación en tres variables binarias independientes, en lugar de una única variable categórica de múltiples niveles, permite al modelo tratar cada dimensión del intento de acceso de forma autónoma, facilitando la identificación de patrones como el uso sistemático de credenciales por defecto típico de ataques automatizados dirigidos a equipos industriales.

#### Modbus TCP
Del servidor Modbus TCP se extraerán: el código de función utilizado en la solicitud, el número de registros accedidos o modificados durante la sesión, la frecuencia de acceso expresada como número de solicitudes por unidad de tiempo, el tipo de operación realizada, distinguiendo entre lectura y escritura, y la dirección inicial del registro accedido. Esta última variable resulta especialmente relevante dado que, en un sistema de control industrial, los registros de bajo rango suelen corresponder a telemetría de operación, mientras que los registros de rangos superiores pueden corresponder a parámetros de configuración crítica del sistema, lo que convierte la dirección de acceso en un indicador significativo del nivel de peligrosidad de la interacción.

#### MQTT
Del bróker MQTT se extraerán: el tópico al que se suscribió o hacia el que se publicó el mensaje, el tamaño del mensaje en bytes, la frecuencia de publicación expresada como número de mensajes por unidad de tiempo y el tipo de operación MQTT realizada, distinguiendo entre operaciones de publicación y suscripción. Esta distinción es relevante porque una suscripción masiva a múltiples tópicos representa un comportamiento diferente al de una publicación de comandos no autorizados, y ambos patrones pueden indicar intenciones maliciosas distintas que el modelo deberá ser capaz de diferenciar.

#### Red general
A nivel de red se considerarán las siguientes variables transversales a todos los protocolos: puerto de destino, tasa de paquetes por segundo, total de bytes transmitidos durante la sesión, duración total del flujo de red y número de conexiones iniciadas desde el mismo origen. Con respecto a la dirección IP de origen, si bien será almacenada en la base de datos como atributo de valor forense, se evaluará su exclusión del vector de entrada al modelo, dado que incluirla podría llevar al clasificador a asociar direcciones específicas con comportamiento malicioso en lugar de aprender patrones generalizables de ataque, lo cual comprometería su desempeño ante direcciones IP no vistas durante el entrenamiento. En caso de que la captura de tráfico lo permita, se contempla también la inclusión de flags TCP como variable adicional.

### Variables dependientes.

La variable dependiente corresponde a la clase o etiqueta que el modelo deberá asignar a cada sesión analizada. Se definen siete clases mutuamente excluyentes que representan los tipos de evento que el sistema de detección de intrusiones deberá ser capaz de identificar:

#### Clase 0 (Normal):

Se refiere a todo tráfico legítimo sin indicios de actividad maliciosa que implique alguna amenaza para el sistema.

#### Clase 1 (Escaneo):

Indica la exploración de puertos o descubrimiento de servicios activos en la red del sistema.

#### Clase 2 (Fuerza bruta):

Son todos los intentos repetidos y automatizados de autenticación sobre el servicio SSH del sistema.

#### Clase 3 (Manipulación Modbus/MQTT):

Intentos de lectura o escritura no autorizada sobre registros del servidor Modbus TCP, o manipulación indebida de tópicos MQTT mediante publicaciones o suscripciones no legítimas.

#### Clase 4 (DoS/DDoS):

Son las inundaciones de conexiones o solicitudes con el fin de saturar un servicio disponible.

#### Clase 5 (Ataque de Repetición - RA).

Consiste en capturar y reenviar de forma diferida tramas legítimas de Modbus TCP o MQTT (como órdenes de apagado) para forzar acciones no autorizadas. Su peligro radica en que el contenido del mensaje es válido, por lo que su detección depende de identificar anomalías en el patrón temporal o ciclos inusuales de transmisión.

#### Clase 6 (Inyección de Datos Falsos - FDIA).

Consiste en modificar maliciosamente los valores de variables físicas (como irradiancia o potencia) en los registros Modbus o payloads MQTT para engañar al sistema de monitoreo. A diferencia de un ataque volumétrico, no busca interrumpir el servicio, sino degradar el sistema de manera silenciosa induciendo decisiones erróneas en el SCADA.

Estas siete clases fueron seleccionadas por representar tanto los vectores de ataque tradicionales reportados en la literatura sobre sistemas de detección de intrusiones industriales, como amenazas específicas del dominio ciberfísico fotovoltaico, particularmente los ataques de repetición (RA) y de inyección de datos falsos (FDIA). Su definición en esta etapa del proyecto establece directamente la estructura del dataset que se construirá durante la fase experimental y orienta el proceso de entrenamiento y evaluación del modelo de Machine Learning.

## 5. Flujo metodológico preliminar.

El sistema propuesto opera como un pipeline secuencial e integrado en el que cada componente alimenta al siguiente, desde la generación de telemetría fotovoltaica hasta la visualización de alertas clasificadas. A continuación se describe el flujo completo de interacción entre los módulos que conforman la arquitectura del proyecto.

#### Simulación FV — qué genera.

El flujo se origina en el módulo de simulación fotovoltaica, el cual genera de forma continua telemetría que replica el comportamiento eléctrico y operativo de una planta de generación solar real. A partir de un modelo físico-matemático basado en el modelo de un diodo del generador fotovoltaico y en relaciones de conversión del inversor y datos de irradiancia de la región, el módulo produce variables como voltaje y corriente de entrada al inversor, potencia instantánea generada, temperatura de operación de los paneles, irradiancia solar incidente, estado operativo del sistema y energía acumulada. Esta telemetría es publicada periódicamente a través del bróker MQTT y expuesta simultáneamente mediante el servidor Modbus TCP, de manera que los servicios señuelo del honeypot presenten en todo momento datos operativos dinámicos y físicamente coherentes, lo cual dota al entorno de la credibilidad necesaria para atraer interacciones relevantes.

#### Honeypot — qué captura.

La telemetría generada por la simulación alimenta directamente los servicios señuelo del honeypot, desplegado sobre la Raspberry Pi 4 mediante contenedores Docker. El honeypot expone cuatro superficies de ataque: un servidor SSH, un servidor HTTP que emula la interfaz web de administración del inversor, el servidor Modbus TCP y el bróker MQTT. Dado que los servicios expuestos no forman parte de ningún flujo operativo legítimo, toda interacción que se produzca con alguno de ellos es considerada por definición como un evento de interés para el sistema, lo cual simplifica el proceso de etiquetado y elimina la necesidad de filtrar tráfico autorizado durante la construcción del dataset. El honeypot captura, por protocolo, las credenciales de autenticación y comandos ejecutados en sesiones SSH, las solicitudes de lectura o escritura sobre registros Modbus TCP junto con sus direcciones y códigos de función, las operaciones de publicación y suscripción realizadas sobre tópicos MQTT, y los parámetros de red transversales como puerto de destino, tamaño del payload, tasa de paquetes y duración de la sesión. Para la captura de sesiones SSH se empleará la herramienta Cowrie, mientras que el tráfico de red será registrado mediante tcpdump para su posterior análisis.

Los archivos de captura generados por tcpdump en formato PCAP serán procesados mediante el Parser Python, el cual extraerá los atributos de red relevantes de cada flujo, como puerto de destino, duración, tasa de paquetes y bytes transmitidos, y los normalizará en registros estructurados compatibles con el esquema de la base de datos, donde serán persistidos junto con los eventos capturados por Cowrie bajo un identificador de sesión común que permite correlacionar ambas fuentes durante la construcción del dataset.

#### Base de datos — qué almacena.

Cada evento capturado por el honeypot será almacenado en una base de datos relacional. Inicialmente, se utilizará SQLite debido a su simplicidad y bajo consumo de recursos, facilitando el desarrollo y validación del prototipo sobre Raspberry Pi 4. Los registros incluirán información temporal, atributos específicos de cada protocolo (SSH, Modbus TCP y MQTT) y parámetros generales de red. En fases posteriores se contempla la migración hacia PostgreSQL si el volumen de datos o los requerimientos de concurrencia del sistema así lo demandan. La estructura lógica del esquema será diseñada desde el inicio para garantizar compatibilidad entre ambos motores.

#### Dataset — ¿cómo se construye?

Los eventos almacenados en la base de datos serán extraídos y transformados para construir el conjunto de datos empleado por el modelo de machine learning. El proceso incluirá limpieza, normalización, ingeniería de características y etiquetado manual de las sesiones según las categorías de tráfico definidas. Posteriormente, el dataset será dividido para entrenamiento y evaluación del clasificador.

#### Random Forest — qué clasifica.

El dataset procesado será utilizado para entrenar un clasificador Random Forest encargado de asignar una de las siete clases definidas a cada evento registrado. El entrenamiento incluirá partición entrenamiento-prueba, ajuste de hiperparámetros y evaluación mediante precisión, recall, F1-score y matriz de confusión. Una vez validado, el modelo será integrado al sistema para clasificar nuevos eventos capturados por el honeypot.

#### Dashboard — qué visualiza.

Los resultados de clasificación producidos por el modelo, junto con la telemetría activa de la simulación fotovoltaica, convergen en un panel de visualización unificado. El dashboard presentará en tiempo casi real las alertas generadas por el sistema con su clasificación por tipo de ataque, la frecuencia e historial de eventos detectados, los servicios más frecuentemente atacados y los parámetros operativos actuales de la planta simulada, como potencia generada, estado del inversor y variables ambientales. Este panel constituirá la interfaz final del sistema y permitirá evaluar de forma integral el comportamiento del honeypot y la capacidad de respuesta del módulo de detección durante las pruebas experimentales, permitiendo correlacionar los eventos de ciberseguridad con el comportamiento operativo de la planta simulada.