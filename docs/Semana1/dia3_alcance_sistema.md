## Alcance general del sistema.

El presente proyecto diseña e implementa un sistema de seguridad ciberfísica orientado a infraestructuras de generación solar fotovoltaica, cuyo propósito central es capturar, estructurar y clasificar eventos asociados a amenazas dirigidas a entornos fotovoltaicos simulados. El contexto de aplicación corresponde a los sistemas de monitoreo y control (SCADA) propios de plantas fotovoltaicas modernas, los cuales integran protocolos de comunicación industrial como Modbus TCP, característico de entornos de tecnología operacional, y MQTT, ampliamente adoptado en infraestructuras de Internet Industrial de las Cosas. Esta convergencia entre el dominio OT y el dominio IIoT amplía la superficie de ataque de dichas instalaciones y genera la necesidad de contar con entornos controlados que permitan estudiar el comportamiento de amenazas cibernéticas sin comprometer sistemas de producción reales.

Para dar respuesta a esta necesidad, el sistema propuesto se articula en seis componentes interconectados: un módulo de simulación fotovoltaica genera telemetría continua y físicamente coherente a partir del modelo de un diodo del generador fotovoltaico complementado con relaciones simplificadas de conversión del inversor, la cual es expuesta a través de los servicios Modbus TCP y MQTT del honeypot para dotar al entorno señuelo de credibilidad operativa. El honeypot, desplegado sobre una Raspberry Pi 4 mediante contenedores Docker, expone además servicios SSH y HTTP que emulan los puntos de acceso típicos de una instalación fotovoltaica conectada en red, registrando toda interacción como un evento estructurado. Dichos eventos serán persistidos en una base de datos relacional implementada inicialmente sobre SQLite, debido a su simplicidad y bajo consumo de recursos, lo que facilita el diseño y la validación del prototipo en la Raspberry Pi. En una segunda etapa, se migrará hacia PostgreSQL para satisfacer los requerimientos de volumen de datos y concurrencia que demande el sistema. Desde esta base de datos se construye un dataset etiquetado mediante extracción de características por protocolo, ingeniería de atributos y etiquetado manual por clase de ataque. Sobre este dataset se entrena un clasificador basado en el algoritmo Random Forest, cuya salida es visualizada en un dashboard unificado que presenta tanto las alertas de intrusión clasificadas como la telemetría activa de la planta simulada.

El alcance del sistema se delimita a un entorno de laboratorio en el que los ataques son generados de forma controlada, abarcando siete categorías de eventos: tráfico normal, escaneo de puertos, fuerza bruta SSH, acceso no autorizado sobre Modbus TCP y MQTT, denegación de servicio, ataque de repetición e inyección de datos falsos. El sistema no tiene como objetivo operar en producción ni proteger infraestructuras reales durante el período de desarrollo, sino generar evidencia empírica suficiente para validar la viabilidad técnica de la propuesta como herramienta de detección de intrusiones en el dominio específico de la ciberseguridad fotovoltaica.

## Funcionalidades incluidas.

El sistema sí realizará las siguientes funcionalidades:

#### Simulación fotovoltaica.

- Generación continua de telemetría fotovoltaica con variables eléctricas físicamente coherentes.
- Publicación periódica de datos mediante protocolo MQTT y exposición vía servidor Modbus TCP.

#### Honeypot.

- Despliegue de servicios señuelo SSH (puerto 22), HTTP (puerto 80), Modbus TCP (puerto 502) y MQTT (puerto 1883).
- Captura de sesiones SSH mediante Cowrie con registro de credenciales, comandos y duración.
- Registro de tráfico de red mediante tcpdump en formato PCAP.
  
#### Procesamiento.
 
- Conversión de archivos PCAP a eventos estructurados mediante scripts Python, extrayendo atributos de flujo como duración, bytes, paquetes, conexiones y flags TCP.
  
#### Almacenamiento.

- Persistencia de todos los eventos capturados en base de datos SQLite durante la fase de prototipo, con migración posterior a PostgreSQL.

#### Dataset.

- Construcción del dataset mediante ingeniería de características, etiquetado manual por clase y división en conjuntos de entrenamiento y prueba.
  
#### Machine Learning.

- Entrenamiento de un clasificador Random Forest sobre el dataset construido.
- Evaluación del modelo mediante métricas estándar e importancia de variables.
  
#### Dashboard.

- Visualización unificada de alertas de intrusión clasificadas por tipo de ataque.
- Visualización de telemetría activa de la planta fotovoltaica simulada en tiempo casi real.

## Exclusiones del proyecto.

El sistema no realizará las siguientes funciones, las cuales quedan explícitamente fuera del alcance del presente proyecto:

#### Operación industrial.

- El sistema no protegerá plantas fotovoltaicas reales ni será desplegado en entornos de producción.
  
#### Respuesta automática.

- El sistema no bloqueará atacantes, no emitirá contramedidas activas ni modificará configuraciones de red en respuesta a eventos detectados.
  
#### Inteligencia artificial avanzada.

- No se utilizarán técnicas de aprendizaje profundo ni el modelo realizará aprendizaje continuo o actualización automática.

#### Hardware industrial.

- No se emplearán controladores lógicos programables reales ni inversores solares comerciales físicos.

#### Generalización.

- El sistema no garantizará detección universal de amenazas ni cubrirá la totalidad de protocolos OT existentes.

## Alcance del módulo de simulación FV.

El módulo de simulación generará de forma continua las siguientes variables físicas y operativas de la planta fotovoltaica:

- Voltaje de corriente continua en la entrada del inversor.
- Corriente de corriente continua.
- Potencia instantánea generada.
- Irradiancia solar incidente.
- Temperatura de operación de los paneles.
- Energía acumulada expresada en kilovatios-hora.
- Estado operativo del inversor (activo, falla, apagado).

El comportamiento eléctrico del sistema será calculado a partir del modelo de un diodo del panel fotovoltaico, ampliamente utilizado en la literatura de sistemas de energía renovable. Los valores de irradiancia utilizados como señal de entrada al modelo serán obtenidos de fuentes públicas de acceso libre, como la API NASA POWER, garantizando coherencia con las condiciones climáticas de la región donde se contextualiza el proyecto. La telemetría generada será publicada periódicamente mediante el protocolo MQTT y expuesta simultáneamente a través de un servidor Modbus TCP con registros mapeados conforme a especificaciones de equipos de referencia del sector.

## Alcance del honeypot.

El honeypot expondrá cuatro servicios señuelo sobre la Raspberry Pi 4, cada uno asociado a un puerto específico:


| Servicio   | Puerto   | Función señuelo                                          |
|------------|----------|----------------------------------------------------------|
| SSH        | 22       | Terminal de administración remota del inversor.          |
| HTTP       | 80       | Interfaz web de administración del sistema fotovoltaico. |
| Modbus TCP | 502      | Servidor de registros del inversor solar.                |
| MQTT       | 1883     | Bróker de telemetría de la planta.                       |

La captura se realizará por protocolo de la siguiente manera:

#### SSH — Cowrie

- Nombres de usuario y contraseñas intentados.
- Comandos ejecutados durante la sesión.
- Duración total de la sesión.

#### HTTP

- Solicitudes realizadas al servidor.
- Recursos accedidos o consultados.

#### Modbus TCP

- Código de función utilizado en cada solicitud.
- Dirección inicial del registro accedido.
- Número de registros leídos o escritos.

#### MQTT

- Tópicos suscritos o publicados.
- Contenido y tamaño del payload.
- Frecuencia de publicación.

#### Red general — tcpdump + Parser Python

- Archivos PCAP procesados mediante script Python que extraerá atributos de flujo: duración, bytes transmitidos, número de paquetes, conexiones iniciadas y flags TCP. Estos atributos serán normalizados e insertados como registros estructurados en la base de datos, compartiendo un identificador de sesión común con los logs de Cowrie.

## Alcance de la base de datos.

La base de datos constituye el repositorio central de todos los eventos capturados por el honeypot. Durante la fase de prototipo se implementará sobre SQLite, y se almacenarán los siguientes elementos:

- Eventos capturados por Cowrie (sesiones SSH).
- Eventos procesados desde archivos PCAP mediante el parser Python.
- Marcas temporales de cada evento registrado.
- Atributos de sesión extraídos por protocolo.
- Dirección IP de origen con fines forenses exclusivamente.
- Etiquetas de clase asignadas manualmente durante la construcción del dataset.

Se contempla la migración hacia PostgreSQL en una etapa posterior, en caso de que el volumen de eventos recolectados o los requerimientos de concurrencia del sistema superen las capacidades de SQLite.

## Alcance del dataset.

El dataset de entrenamiento y evaluación del modelo será construido a partir de los registros almacenados en la base de datos, siguiendo las etapas que se describen a continuación:

- Extracción de registros desde la base de datos para cada sesión capturada.
- Limpieza y normalización de valores atípicos o registros incompletos.
- Ingeniería de características mediante la derivación de atributos relevantes por protocolo.
- Etiquetado manual de cada sesión según la clase de evento correspondiente.
- División del dataset en conjuntos de entrenamiento y prueba.
  
Las clases contempladas en el dataset son las siguientes:

- Clase 0 — Normal: tráfico legítimo sin indicios de actividad maliciosa.
- Clase 1 — Escaneo: exploración de puertos o descubrimiento de servicios.
- Clase 2 — Fuerza bruta: intentos repetidos de autenticación sobre SSH.
- Clase 3 — Manipulación Modbus/MQTT: lectura o escritura no autorizada sobre registros Modbus TCP o manipulación indebida de tópicos MQTT.
- Clase 4 — DoS/DDoS: inundación de conexiones con el fin de saturar un servicio.
- Clase 5 — Ataque de Repetición - RA: reenvío diferido de tramas legítimas para forzar acciones no autorizadas.
- Clase 6 — Inyección de Datos Falsos - FDIA: modificación maliciosa de variables físicas en registros Modbus o payloads MQTT para inducir decisiones erróneas en el sistema de monitoreo.

## Alcance del modelo de Machine Learning.

El módulo de aprendizaje automático realizará las siguientes funciones:

#### Sí realizará

- Clasificación supervisada de eventos de red en las siete clases predefinidas.
- Entrenamiento offline sobre el dataset etiquetado construido durante la fase experimental.
- Evaluación del desempeño mediante métricas estándar: precisión, recall, puntuación F1 y matriz de confusión.
- Análisis de importancia de variables para identificar los atributos más relevantes en la clasificación.

#### No realizará

- No garantizará la detección de ataques de tipo zero-day no representados en el dataset de entrenamiento.
- No realizará aprendizaje continuo ni se actualizará automáticamente con nuevos eventos.

## Alcance del dashboard.

El panel de visualización será desarrollado en Streamlit durante la fase inicial del proyecto y presentará la siguiente información:

- Alertas de intrusión en tiempo casi real con su clasificación por tipo de ataque.
- Historial de eventos detectados con marca temporal y protocolo involucrado.
- Distribución de ataques por clase mediante gráficos estadísticos.
- Métricas de desempeño del modelo: precisión, recall y F1-score.
- Telemetría activa de la planta fotovoltaica simulada: potencia generada, estado del inversor y variables ambientales.

Se contempla la integración futura con Grafana para ampliar las capacidades de visualización y monitoreo en caso de requerirse mayor flexibilidad en la presentación de datos.

## Criterios de éxito del proyecto.

El proyecto será considerado exitoso cuando se cumplan los siguientes criterios de aceptación por componente:

| Componente       | Criterio de éxito                                        |
|------------------|----------------------------------------------------------|
| Simulación FV    | Las variables generadas mantienen coherencia física con el comportamiento esperado de una planta fotovoltaica real, con una desviación porcentual menor al 5%.                                                       |
| Honeypot         | El sistema capturará eventos estructurados correspondientes a los tipos de ataque reproducibles experimentalmente en el entorno de laboratorio, garantizando al menos la obtención de muestras de escaneo de puertos, fuerza bruta SSH y manipulación no autorizada sobre Modbus TCP y MQTT. Para las clases cuya generación controlada resulte inviable en el entorno de pruebas, como el ataque de repetición y la inyección de datos falsos, la ausencia de capturas propias será compensada mediante la incorporación de muestras provenientes de datasets públicos de referencia en la etapa de construcción del dataset, garantizando así la representatividad de las siete clases definidas.                                                                    |
| Base de datos    | Todos los eventos capturados son almacenados correctamente como registros estructurados con sus atributos completos y marca temporal.         |
| Dataset          | El dataset contendrá muestras representativas de las siete clases definidas. Las clases capturadas directamente por el honeypot constituirán la fuente primaria del conjunto de datos; en los casos en que la captura experimental no sea suficiente o no sea posible, particularmente para las clases de ataque de repetición e inyección de datos falsos, se complementará con muestras provenientes de datasets públicos de referencia en el área, procurando en todo caso minimizar el desbalance entre categorías mediante estrategias de recolección controlada y ponderación durante el entrenamiento.                                                                |
| Machine Learning | El clasificador Random Forest alcanza una precisión, recall y puntuación F1 iguales o superiores al 90% en el conjunto de prueba.                                                                       |
| Dashboard        | La visualización es funcional, se presenta con actualización periódica durante las pruebas experimentales y muestra la telemetría activa de la planta simulada de forma legible.                                                                      |
