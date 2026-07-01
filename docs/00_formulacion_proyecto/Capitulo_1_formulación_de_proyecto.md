# Capítulo 1. Formulación del Proyecto

**Diseño e implementación de un honeypot inteligente para la detección de amenazas cibernéticas en infraestructuras fotovoltaicas mediante técnicas de aprendizaje automático**

*Trabajo de grado — Programa de Ingeniería Electrónica, Universidad Santo Tomás*

---

## 1. Introducción

La transición energética mundial ha posicionado a la generación solar fotovoltaica como uno de los pilares fundamentales para la descarbonización de la matriz eléctrica. Las plantas fotovoltaicas modernas dejaron de ser instalaciones aisladas para convertirse en nodos activos e interconectados del sistema eléctrico de potencia, integrando capas digitales completas de supervisión, control y adquisición de datos (SCADA) que permiten monitorear la producción energética en tiempo real, gestionar alarmas, modificar parámetros de operación del inversor y, en muchos casos, controlar remotamente la planta sin necesidad de presencia física. Esta digitalización, que ha mejorado sustancialmente la eficiencia operativa y reducido los costos de mantenimiento del sector, trae consigo una contraparte ineludible: el incremento significativo de la superficie de ataque de la infraestructura energética.

La arquitectura de comunicaciones de una planta fotovoltaica típica converge hoy entre la tecnología operacional (OT), la tecnología de la información (TI) y el Internet Industrial de las Cosas (IIoT), apoyándose en protocolos como Modbus TCP, ampliamente utilizado en las redes de área local industrial para la comunicación maestro-esclavo entre el sistema SCADA, los registradores de datos y los inversores, y MQTT, protocolo ligero de tipo publicación-suscripción empleado para transmitir telemetría IIoT hacia plataformas de supervisión alojadas en la nube. Ambos protocolos fueron diseñados bajo criterios que privilegian la disponibilidad continua y la baja latencia del control en tiempo real, omitiendo de forma intencional mecanismos nativos de cifrado y autenticación fuerte. Esta carencia estructural convierte a Modbus TCP y a MQTT en superficies de ataque particularmente vulnerables frente a técnicas de interceptación de tráfico (*sniffing*), suplantación de identidad (*spoofing*) y manipulación de intermediarios (*Man-in-the-Middle*).

La pertinencia de esta problemática no es de naturaleza hipotética. Reportes recientes de firmas de investigación en ciberseguridad especializadas en infraestructura crítica, como Forescout Vedere Labs, documentaron en 2025 un total de 46 vulnerabilidades nuevas en inversores solares de fabricantes con participación relevante del mercado global —entre ellos Sungrow, Growatt y SMA—, de las cuales el 80 % fueron clasificadas con severidad alta o crítica. De manera más contundente, en mayo de 2024 se reportó el secuestro de cerca de 800 dispositivos de monitoreo remoto SolarView Compact instalados en plantas fotovoltaicas japonesas, episodio que constituye el primer ciberataque públicamente confirmado sobre infraestructura de generación solar. Esta evidencia, sumada a la publicación por parte del Instituto Nacional de Estándares y Tecnología de los Estados Unidos (NIST) de una guía dedicada exclusivamente a la ciberseguridad de inversores inteligentes (NIST IR 8498), confirma que la comunidad académica e industrial reconoce esta problemática como una amenaza activa, creciente y de relevancia institucional.

Frente a este panorama, el ejercicio investigativo y experimental sobre estas amenazas se ve limitado por una restricción metodológica de fondo: las normativas de seguridad eléctrica y la naturaleza crítica de la infraestructura impiden la simulación de vectores de ataque, como la inyección de datos falsos o los ataques de repetición, en entornos de producción reales. Esta imposibilidad técnica genera un vacío concreto en la disponibilidad de datos de tráfico anómalo etiquetado, indispensable para el entrenamiento de algoritmos de aprendizaje automático orientados a la detección de intrusiones en sistemas de control industrial fotovoltaico.

En respuesta a esta necesidad, el presente trabajo de grado propone el diseño e implementación de un honeypot inteligente especializado en infraestructuras fotovoltaicas. El sistema propuesto integra seis componentes interconectados que conforman un flujo experimental completo: un módulo de simulación físico-matemática que genera telemetría fotovoltaica físicamente coherente; un honeypot de media interacción desplegado sobre una Raspberry Pi 4, que expone servicios señuelo SSH, HTTP, Modbus TCP y MQTT; una base de datos que persiste los eventos capturados; un proceso de construcción de un dataset etiquetado; un clasificador basado en el algoritmo Random Forest encargado de distinguir entre tráfico legítimo y siete categorías de amenazas; y un dashboard de visualización que integra los resultados de clasificación con la telemetría operativa de la planta simulada. El sistema se enmarca dentro de un nivel de madurez tecnológica TRL 5, correspondiente a una tecnología validada en un entorno relevante mediante experimentación controlada de laboratorio.

El presente capítulo desarrolla la formulación completa del proyecto. En primer lugar, se presenta la justificación que sustenta la pertinencia académica, técnica, social y disciplinar de la investigación. A continuación, se establecen el objetivo general y los objetivos específicos que orientan el desarrollo del trabajo, seguidos de la delimitación precisa del alcance y de las restricciones que enmarcan el proyecto. Posteriormente se describen los aportes esperados como resultado de la investigación, se analiza la viabilidad técnica, económica, operativa y ética de su ejecución, y finalmente se presentan las variables de investigación que serán objeto de medición durante la fase experimental. Esta estructura garantiza la coherencia entre el problema identificado, los objetivos planteados y la metodología de validación que se desarrollará en los capítulos posteriores del documento.

---

## 2. Justificación

La pertinencia del presente proyecto se sustenta sobre cuatro ejes complementarios: un vacío de investigación identificado en la literatura científica, evidencia documentada de incidentes reales sobre infraestructura solar, las consecuencias técnicas y económicas que se derivan de la materialización de estas amenazas, y la coherencia del proyecto con las líneas de investigación institucionales de la Facultad de Ingeniería Electrónica de la Universidad Santo Tomás.

**Justificación científica.** La revisión sistemática de literatura realizada durante la fase de estado del arte del proyecto permitió identificar tres líneas de trabajo consolidadas en torno a los honeypots industriales: honeypots de baja interacción orientados a la recolección de inteligencia de amenazas a gran escala sobre dispositivos ICS expuestos en Internet (Grigoriou et al., 2023), honeypots de media interacción integrados con algoritmos de clasificación supervisada sobre tráfico Modbus TCP (Radoglou-Grammatikis et al., 2020), y honeypots adaptativos orientados específicamente al protocolo MQTT en entornos IIoT. Sin embargo, ninguno de los trabajos revisados integra de forma simultánea un módulo de simulación física del proceso industrial, la exposición conjunta de protocolos OT (Modbus TCP) e IIoT (MQTT), y un clasificador de aprendizaje automático, dentro del dominio específico de la generación solar fotovoltaica. Este vacío de investigación, identificado de manera explícita durante la revisión bibliográfica, constituye la justificación científica central del proyecto: la propuesta no construye un honeypot de forma arbitraria, sino que responde a una intersección no cubierta previamente en la literatura, adoptando el pipeline honeypot-base de datos-clasificador validado metodológicamente por trabajos previos y extendiéndolo hacia un dominio de aplicación poco explorado.

**Justificación técnica y de pertinencia industrial.** La evidencia documentada confirma que la vulnerabilidad de la infraestructura solar conectada no constituye un escenario hipotético. El informe *SUN:DOWN* de Forescout Vedere Labs (2025) reportó un promedio sostenido de diez vulnerabilidades divulgadas por año en inversores solares comerciales durante los últimos tres años, mientras que un informe de seguimiento de la misma organización identificó cerca de 35.000 dispositivos solares con interfaces de administración expuestas directamente en Internet a través del motor de búsqueda Shodan. El caso del secuestro de los dispositivos SolarView Compact en Japón evidenció, además, una brecha crítica entre la disponibilidad de parches de seguridad y su aplicación efectiva por parte de los operadores, patrón recurrente en infraestructuras OT donde los ciclos de mantenimiento son menos frecuentes que en sistemas de tecnología de la información convencionales. Esta evidencia justifica técnicamente la necesidad de mecanismos de detección activa, como el honeypot propuesto, que no dependan exclusivamente de la diligencia del operador para identificar actividad maliciosa.

**Justificación social y económica.** La materialización de amenazas como la denegación de servicio, la manipulación *Man-in-the-Middle* o la inyección de datos falsos sobre infraestructuras fotovoltaicas trasciende el ámbito puramente informático y se traduce en consecuencias físicas y económicas concretas. La alteración de las curvas de inyección de potencia activa y reactiva mediante ataques de inyección de datos falsos puede impactar el balance carga-generación del sistema interconectado nacional, incrementando el riesgo de desviaciones de frecuencia y voltaje que comprometen el cumplimiento de códigos de red como el IEEE 1547. De manera análoga, la manipulación sutil de variables operativas puede inducir pérdidas económicas directas por la limitación injustificada de la potencia inyectada, así como penalizaciones regulatorias por incumplimiento de las consignas de despacho. En el escenario más severo, la manipulación del firmware o de los registros de configuración interna del inversor puede forzar ciclos de conmutación inadecuados sobre los módulos de potencia (IGBT), provocando sobrecalentamientos y fallas catastróficas cuya reparación implica costos elevados y prolongados tiempos de importación de componentes. Estas consecuencias justifican, desde una perspectiva social y económica, la pertinencia de investigar mecanismos que permitan caracterizar y anticipar este tipo de amenazas antes de que se materialicen sobre infraestructura real.

**Justificación institucional y disciplinar.** El proyecto se enmarca dentro de la línea de investigación institucional de Automática y Sistemas Inteligentes de la Universidad Santo Tomás, integrando además componentes de sistemas de energía eléctrica, ciberseguridad industrial y aprendizaje automático. Si bien el contexto de aplicación corresponde al sector energético, el eje central de la investigación reside en el desarrollo de un sistema electrónico inteligente que articula automatización, monitoreo y técnicas de inteligencia computacional, lo cual resulta coherente con los objetivos formativos del programa de Ingeniería Electrónica y con las capacidades de investigación aplicada que la Facultad busca consolidar a través de sus grupos de investigación.

En conjunto, estos cuatro ejes —el vacío científico identificado, la evidencia técnica de vulnerabilidad real, las consecuencias económicas y sociales de su explotación, y la coherencia con las líneas institucionales de investigación— constituyen la base sobre la cual se formulan el objetivo general y los objetivos específicos que se presentan a continuación.

---

## 3. Objetivo General

Diseñar e implementar un honeypot inteligente de media interacción, integrado con un módulo de simulación físico-matemática de una planta fotovoltaica y un clasificador basado en el algoritmo Random Forest, que permita capturar, estructurar y clasificar eventos de ciberseguridad asociados a amenazas dirigidas a infraestructuras fotovoltaicas, validando experimentalmente su desempeño mediante escenarios controlados de ataque en un entorno de laboratorio.

---

## 4. Objetivos Específicos

Con el propósito de operacionalizar el objetivo general en componentes evaluables y secuenciales, coherentes con el flujo metodológico del sistema descrito en la introducción de este capítulo, se plantean los siguientes objetivos específicos:

1. **Diseñar la arquitectura técnica del sistema**, definiendo los componentes, protocolos de comunicación, flujos de información y esquema de base de datos que permitan la integración coherente del módulo de simulación fotovoltaica, el honeypot, el clasificador de aprendizaje automático y el panel de visualización.

2. **Implementar un módulo de simulación fotovoltaica** capaz de generar telemetría continua y físicamente coherente —voltaje, corriente, potencia instantánea, irradiancia, temperatura de operación y energía acumulada— a partir del modelo de un diodo del generador fotovoltaico, complementado con datos históricos de irradiancia solar de la región, y exponerla mediante los protocolos Modbus TCP y MQTT.

3. **Desplegar un honeypot de media interacción sobre una Raspberry Pi 4**, exponiendo cuatro servicios señuelo representativos del dominio fotovoltaico (SSH, HTTP, Modbus TCP y MQTT), y configurar la captura estructurada de los eventos de interacción registrados en cada uno de ellos.

4. **Construir un dataset etiquetado** a partir de los eventos capturados por el honeypot, mediante procesos de limpieza, normalización, ingeniería de características por protocolo y etiquetado manual conforme a las siete clases de tráfico definidas para el estudio, complementando con datasets públicos de referencia las categorías cuya generación experimental resulte inviable en el entorno de laboratorio.

5. **Entrenar y evaluar un clasificador basado en el algoritmo Random Forest** sobre el dataset construido, determinando su desempeño mediante métricas estándar de clasificación —precisión, exhaustividad, puntuación F1 y matriz de confusión— y analizando la importancia relativa de las variables empleadas como entrada del modelo.

6. **Desarrollar un dashboard de visualización** que integre las alertas de intrusión clasificadas por el modelo con la telemetría activa de la planta fotovoltaica simulada, permitiendo el monitoreo casi en tiempo real del comportamiento del sistema durante las pruebas experimentales.

La consecución secuencial de estos seis objetivos específicos conduce directamente al cumplimiento del objetivo general, en la medida en que cada uno constituye un eslabón necesario del pipeline experimental: la arquitectura orienta el diseño, la simulación dota de credibilidad al entorno señuelo, el honeypot captura la evidencia, el dataset estructura dicha evidencia, el clasificador la interpreta, y el dashboard la comunica de forma comprensible.

---

## 5. Alcance

El presente proyecto comprende el diseño e implementación de un sistema de seguridad ciberfísica de carácter experimental, orientado a infraestructuras de generación solar fotovoltaica, cuyo propósito central es capturar, estructurar y clasificar eventos asociados a amenazas cibernéticas en un entorno fotovoltaico simulado. El sistema opera enteramente dentro de un entorno de laboratorio controlado, en el cual los ataques se generan de forma deliberada y supervisada, sin que en ningún momento se comprometan sistemas de producción reales ni infraestructura eléctrica en operación.

El alcance del sistema se articula alrededor de los seis componentes descritos en los objetivos específicos, cada uno con funcionalidades claramente delimitadas:

**Simulación fotovoltaica.** El sistema generará de forma continua telemetría con variables eléctricas físicamente coherentes —voltaje y corriente de entrada al inversor, potencia instantánea, irradiancia solar incidente, temperatura de operación de los paneles, energía acumulada y estado operativo del inversor—, publicándola periódicamente mediante el protocolo MQTT y exponiéndola simultáneamente a través de un servidor Modbus TCP con registros mapeados conforme a especificaciones de equipos de referencia del sector.

**Honeypot.** Se desplegarán cuatro servicios señuelo sobre una Raspberry Pi 4 mediante contenedores Docker: un servidor SSH en el puerto 22, capturado mediante la herramienta Cowrie; un servidor HTTP en el puerto 80, que emula la interfaz web de administración del inversor; un servidor Modbus TCP en el puerto 502; y un bróker MQTT en el puerto 1883. El tráfico de red asociado a estos servicios será adicionalmente capturado mediante la herramienta tcpdump en formato PCAP.

**Procesamiento y almacenamiento.** Los archivos de captura PCAP serán procesados mediante scripts en Python que extraerán los atributos de flujo relevantes para cada sesión, los cuales serán normalizados y persistidos, junto con los eventos capturados por Cowrie, en una base de datos relacional implementada inicialmente sobre SQLite, contemplándose su migración hacia PostgreSQL en una etapa posterior según los requerimientos de volumen y concurrencia del sistema.

**Dataset y aprendizaje automático.** A partir de los eventos almacenados se construirá un dataset mediante ingeniería de características y etiquetado manual, el cual será dividido en conjuntos de entrenamiento y prueba para el entrenamiento de un clasificador Random Forest, encargado de asignar cada evento a una de siete clases mutuamente excluyentes: tráfico normal, escaneo de puertos, fuerza bruta o intrusión SSH, manipulación no autorizada sobre Modbus TCP o MQTT, denegación de servicio, ataque de repetición e inyección de datos falsos.

**Dashboard.** Se desarrollará un panel de visualización en Streamlit que presentará las alertas de intrusión clasificadas por tipo de ataque, el historial de eventos detectados, la distribución de ataques por clase, las métricas de desempeño del modelo y la telemetría activa de la planta simulada, contemplándose la integración futura con Grafana para ampliar las capacidades de monitoreo.

El proyecto será considerado exitoso en la medida en que se cumplan los siguientes criterios de aceptación por componente:

| Componente | Criterio de éxito |
|---|---|
| Simulación FV | Las variables generadas mantienen coherencia física con el comportamiento esperado de una planta real, con una desviación porcentual inferior al 5 %. |
| Honeypot | El sistema captura eventos estructurados correspondientes a los ataques reproducibles experimentalmente en laboratorio (escaneo, fuerza bruta SSH y manipulación Modbus/MQTT como mínimo). |
| Dataset | El conjunto de datos alcanza un mínimo de 500 eventos etiquetados por clase, con un porcentaje de registros incompletos inferior al 5 %, complementando con datasets públicos las clases de generación experimental inviable. |
| Machine Learning | El clasificador Random Forest alcanza una precisión, exhaustividad y puntuación F1 iguales o superiores al 90 % sobre el conjunto de prueba. |
| Dashboard | La visualización es funcional, se actualiza periódicamente durante las pruebas y presenta de forma legible la telemetría activa de la planta simulada. |

Es importante señalar, de manera transversal a todos los componentes, que el alcance definido es coherente con los objetivos de un trabajo de grado de Ingeniería Electrónica: el proyecto se centra en el desarrollo, la integración y la evaluación experimental de un sistema funcional, sin extenderse hacia mecanismos de respuesta autónoma o de prevención automática frente a las amenazas detectadas, lo cual incrementaría significativamente la complejidad del proyecto y excedería el alcance previsto para esta etapa de formación. Esta delimitación se desarrolla con mayor precisión en el apartado siguiente.

---

## 6. Delimitaciones

Con el fin de mantener la viabilidad del proyecto dentro del tiempo y los recursos disponibles para un trabajo de grado de pregrado, se establecen las siguientes delimitaciones de carácter temporal, espacial, técnico y conceptual.

**Delimitación temporal.** El desarrollo experimental del proyecto se circunscribe al cronograma definido para la elaboración del trabajo de grado, abarcando las fases de diseño, implementación, experimentación y evaluación dentro del periodo académico establecido. El nivel de madurez tecnológica objetivo corresponde a TRL 5 —tecnología validada en un entorno relevante—, lo cual implica que el sistema no se proyecta hacia fases posteriores de despliegue comercial o industrial dentro del alcance temporal de este trabajo.

**Delimitación espacial.** El sistema será implementado y evaluado íntegramente dentro de un entorno de laboratorio controlado, sobre hardware de bajo costo (Raspberry Pi 4) y mediante contenedores Docker. En ningún momento el honeypot será desplegado sobre una red de producción real ni conectado a infraestructura eléctrica en operación, lo cual garantiza que la generación controlada de ataques no represente ningún riesgo para sistemas externos al laboratorio.

**Delimitación técnica.** El proyecto excluye explícitamente de su alcance las siguientes funcionalidades:

- *Operación industrial real:* el sistema no protegerá plantas fotovoltaicas reales ni será desplegado en entornos de producción.
- *Respuesta automática:* el sistema no bloqueará atacantes, no emitirá contramedidas activas ni modificará configuraciones de red en respuesta a los eventos detectados; su función se limita a la detección y clasificación.
- *Técnicas de aprendizaje profundo:* el proyecto se limita al uso de algoritmos de aprendizaje automático clásico, particularmente Random Forest, sin incorporar arquitecturas de *deep learning* ni mecanismos de aprendizaje continuo o actualización automática del modelo.
- *Hardware industrial físico:* no se emplearán controladores lógicos programables reales ni inversores solares comerciales físicos; toda la infraestructura fotovoltaica es simulada mediante software.
- *Generalización universal:* el sistema no garantiza la detección de amenazas de tipo *zero-day* no representadas en el dataset de entrenamiento, ni cubre la totalidad de protocolos de tecnología operacional existentes en la industria, limitándose a Modbus TCP y MQTT por ser los de mayor adopción en el dominio fotovoltaico.

**Delimitación conceptual.** El dataset y el clasificador se restringen a siete clases de tráfico previamente definidas y descritas en el apartado de variables de investigación. Los ataques encubiertos (*Covert Attacks*), si bien representan una amenaza documentada en la literatura, no serán incluidos como clase independiente del clasificador, dado que su generación experimental exige un conocimiento profundo del modelo matemático de la planta y la producción de un volumen suficiente de muestras sintéticas, lo cual excede el alcance previsto para un proyecto de pregrado. De igual forma, la dirección IP de origen, si bien será almacenada en la base de datos con fines forenses, se evaluará su exclusión del vector de características de entrada al modelo, con el fin de evitar que el clasificador asocie direcciones específicas con comportamiento malicioso en lugar de aprender patrones generalizables de ataque.

Estas delimitaciones no restringen la posibilidad de que, en trabajos futuros, la arquitectura desarrollada sea extendida hacia otros protocolos industriales, hacia mecanismos de respuesta activa o hacia su validación sobre infraestructura fotovoltaica real; simplemente acotan el alcance verificable dentro del periodo de desarrollo del presente trabajo de grado.

---

## 7. Aportes esperados

El desarrollo del proyecto se proyecta hacia la generación de aportes de naturaleza tanto tecnológica como científica y documental, los cuales se describen a continuación.

**Aporte principal.** El resultado central del proyecto será un honeypot inteligente para la detección de amenazas cibernéticas en infraestructuras fotovoltaicas, capaz de capturar eventos de seguridad, analizar patrones de ataque mediante técnicas de aprendizaje automático y operar dentro de un entorno de simulación representativo, alcanzando un nivel de madurez tecnológica equivalente a TRL 5.

**Aporte científico.** Como se argumentó en la justificación de este capítulo, la revisión del estado del arte identificó la ausencia, dentro de la literatura disponible, de un honeypot que integre de forma simultánea protocolos OT (Modbus TCP) e IIoT (MQTT) con un módulo de simulación física del proceso y un clasificador de aprendizaje automático, dentro del dominio específico de la generación solar fotovoltaica. El presente proyecto se posiciona en dicha intersección, constituyendo un aporte original que extiende hacia un dominio de aplicación poco explorado el pipeline honeypot-base de datos-clasificador validado previamente por la literatura sobre Modbus TCP, y la idoneidad de Random Forest para la clasificación de tráfico industrial tabular.

**Productos complementarios.** Como resultado del desarrollo de la investigación se obtendrán adicionalmente los siguientes productos:

- Una arquitectura de referencia para la integración de honeypots en infraestructuras fotovoltaicas, documentada y reutilizable en proyectos posteriores.
- Un entorno de simulación de planta fotovoltaica con protocolos industriales (Modbus TCP y MQTT), funcional de manera independiente al honeypot.
- Un modelo de aprendizaje automático entrenado y evaluado para la detección de amenazas en el dominio fotovoltaico.
- Un dashboard funcional para la supervisión y visualización de eventos de seguridad.
- Un dataset etiquetado, generado durante la experimentación, que podrá constituir un insumo de referencia para investigaciones futuras en el área.
- Un repositorio de software completamente documentado y versionado bajo control de versiones Git.
- Documentación técnica del sistema desarrollado y el presente documento de tesis con los resultados de la investigación.

Estos productos complementarios serán desarrollados progresivamente durante las distintas fases del proyecto y constituirán la evidencia tangible del cumplimiento de los objetivos específicos planteados, además de facilitar la transferencia de conocimiento y la continuidad del desarrollo en trabajos de grado posteriores.

---

## 8. Viabilidad

El análisis de viabilidad del proyecto se desarrolla desde cuatro dimensiones complementarias: técnica, económica, operativa y ética-legal.

**Viabilidad técnica.** El desarrollo del proyecto se sustenta en un ecosistema de tecnologías de código abierto ampliamente adoptadas tanto en entornos académicos como industriales: Python como lenguaje de programación principal, Docker y Docker Compose para la contenedorización de los servicios, Cowrie como framework de honeypot especializado para servicios SSH, bibliotecas estándar de Machine Learning para Python, y Grafana o Streamlit para la capa de visualización. La selección de estas tecnologías responde a criterios de interoperabilidad, disponibilidad de documentación técnica, soporte activo de la comunidad y reproducibilidad experimental, factores que reducen significativamente el riesgo técnico de implementación. Adicionalmente, la elección del algoritmo Random Forest como clasificador principal se sustenta en evidencia previa de la literatura (Frazão et al., 2018, 2019; Radoglou-Grammatikis et al., 2020), que reporta un desempeño consistente de los modelos de ensamble sobre datos tabulares derivados de protocolos industriales, lo cual reduce la incertidumbre respecto a la factibilidad de alcanzar las métricas de desempeño planteadas en los objetivos.

**Viabilidad económica.** El proyecto no requiere la adquisición de hardware industrial especializado ni de licencias de software propietario, dado que la totalidad de las tecnologías empleadas corresponde a soluciones de código abierto. El único componente físico requerido es una tarjeta de desarrollo Raspberry Pi 4, de costo reducido y fácilmente disponible, sobre la cual se despliega la totalidad del sistema mediante contenedores Docker. Esta característica hace que el proyecto sea ejecutable con los recursos típicamente disponibles para un trabajo de grado de pregrado, sin que se identifiquen restricciones presupuestales que comprometan su desarrollo.

**Viabilidad operativa.** Al tratarse de un sistema enteramente simulado y desplegado en un entorno de laboratorio controlado, el proyecto no depende de la disponibilidad ni del acceso a infraestructura fotovoltaica real, lo cual elimina restricciones de acceso, autorización o coordinación con terceros que de otro modo podrían comprometer el cronograma del proyecto. La generación controlada de ataques dentro del laboratorio, sumada al uso de datasets públicos de referencia para complementar las clases cuya captura experimental resulte limitada, garantiza que el flujo experimental completo —desde la generación de telemetría hasta la visualización de resultados— pueda ejecutarse de manera autónoma por el autor del proyecto dentro del periodo académico previsto.

**Viabilidad ética y legal.** La naturaleza experimental y simulada del sistema elimina cualquier riesgo de afectación a infraestructura energética real o a terceros. Todos los ataques generados durante la fase experimental se ejecutan de forma controlada y exclusivamente dentro del entorno de laboratorio, sobre un sistema fotovoltaico simulado por software, sin interacción con redes de producción ni con datos sensibles de operadores reales. Esta condición es coherente con los principios éticos de la investigación aplicada en ingeniería y con la imposibilidad normativa, señalada en la justificación del proyecto, de ejecutar pruebas de penetración sobre infraestructura eléctrica en operación.

En conjunto, el análisis precedente permite concluir que el proyecto es viable en sus dimensiones técnica, económica, operativa y ética, condición necesaria para sustentar la factibilidad de alcanzar el objetivo general y los objetivos específicos planteados en los apartados anteriores de este capítulo.

---

## 9. Variables de investigación

La validación experimental del sistema requiere de la definición formal de las variables que serán medidas, registradas y analizadas durante la fase experimental del proyecto. Estas se clasifican en variables independientes, correspondientes a los atributos extraídos de cada sesión capturada por el honeypot que constituyen el vector de entrada al modelo de aprendizaje automático, y en una variable dependiente, correspondiente a la clase de tráfico que el modelo deberá predecir.

### 9.1 Variables independientes (características de entrada)

Las variables independientes se organizan según el protocolo o la capa de red de la cual provienen.

**Variables del servicio SSH.** Se extraerán el número de intentos de autenticación realizados durante la sesión, el número de comandos ejecutados una vez establecida la conexión, la duración total de la sesión en segundos, y tres variables binarias independientes derivadas del resultado de autenticación: validez de la credencial empleada, existencia previa del nombre de usuario en el sistema, y correspondencia de la credencial con un valor por defecto conocido. La separación en variables binarias independientes, en lugar de una variable categórica única, permite al modelo identificar patrones como el uso sistemático de credenciales por defecto, característico de ataques automatizados dirigidos a equipos industriales.

**Variables del servicio Modbus TCP.** Se extraerán el código de función utilizado en la solicitud, el número de registros accedidos o modificados durante la sesión, la frecuencia de acceso expresada como solicitudes por unidad de tiempo, el tipo de operación (lectura o escritura) y la dirección inicial del registro accedido, esta última especialmente relevante dado que, en un sistema de control industrial, los registros de rango inferior suelen corresponder a telemetría de operación mientras que los de rango superior corresponden a parámetros de configuración crítica.

**Variables del servicio MQTT.** Se extraerán el tópico de suscripción o publicación, el tamaño del mensaje en bytes, la frecuencia de publicación expresada como mensajes por unidad de tiempo, y el tipo de operación (publicación o suscripción), dado que una suscripción masiva a múltiples tópicos representa un comportamiento distinto al de la publicación de comandos no autorizados.

**Variables transversales de red.** A nivel de red se considerarán el puerto de destino, la tasa de paquetes por segundo, el total de bytes transmitidos, la duración total del flujo y el número de conexiones iniciadas desde el mismo origen. La dirección IP de origen será almacenada con fines forenses, evaluándose su exclusión del vector de entrada al modelo para evitar que el clasificador asocie direcciones específicas con comportamiento malicioso en detrimento de su capacidad de generalización.

### 9.2 Variable dependiente

La variable dependiente corresponde a la clase de tráfico asignada a cada sesión, definida mediante siete categorías mutuamente excluyentes:

| Clase | Etiqueta | Descripción |
|---|---|---|
| 0 | Normal | Tráfico legítimo, sin indicios de actividad maliciosa. |
| 1 | Escaneo | Exploración de puertos o descubrimiento de servicios activos. |
| 2 | Fuerza bruta / Intrusión SSH | Intentos repetidos de autenticación o acceso exitoso seguido de actividad maliciosa sobre el servicio SSH. |
| 3 | Manipulación Modbus/MQTT | Lectura o escritura no autorizada sobre registros Modbus TCP, o manipulación indebida de tópicos MQTT. |
| 4 | DoS/DDoS | Inundación de conexiones o solicitudes orientada a saturar un servicio. |
| 5 | Ataque de repetición (RA) | Reenvío diferido de tramas legítimas para forzar acciones no autorizadas. |
| 6 | Inyección de datos falsos (FDIA) | Modificación maliciosa de variables físicas en registros Modbus o payloads MQTT para inducir decisiones erróneas en el sistema de monitoreo. |

### 9.3 Operacionalización de variables

| Tipo de variable | Indicador | Instrumento de medición | Escala |
|---|---|---|---|
| Independiente — SSH | Intentos de autenticación, comandos ejecutados, duración de sesión, validez de credencial | Logs de Cowrie | Razón / nominal binaria |
| Independiente — Modbus TCP | Código de función, registros accedidos, frecuencia de acceso, tipo de operación, dirección de registro | Logs del servidor Modbus + parser Python | Razón / nominal |
| Independiente — MQTT | Tópico, tamaño de payload, frecuencia de publicación, tipo de operación | Logs del bróker MQTT | Razón / nominal |
| Independiente — Red general | Puerto de destino, tasa de paquetes, bytes transmitidos, duración de flujo, conexiones por origen | Captura tcpdump (PCAP) + parser Python | Razón |
| Dependiente | Clase de evento (0 a 6) | Etiquetado manual durante la construcción del dataset | Nominal (politómica, 7 categorías) |
| Desempeño del modelo | Precisión, exhaustividad (recall), F1-score, exactitud | Evaluación del clasificador sobre conjunto de prueba | Razón (porcentaje) |

La definición formal de estas variables, establecida en esta etapa de formulación del proyecto, determina de manera directa la estructura del dataset que se construirá durante la fase experimental y orienta el proceso de ingeniería de características, entrenamiento y evaluación del modelo de aprendizaje automático que se desarrollará en los capítulos de metodología y resultados del presente documento.

---

*Fin del capítulo de formulación del proyecto.*