## 1. Contexto del sistema.

#### Planta fotovoltaica.

El mundo global se encuentra en una transición energética impulsada por las distintas fuentes de energías renovables entre ellas la solar donde se encuentran las plantas fotovoltaicas los cuales se transformaron en elementos de generación aislados a nodos criticos e interconectados del sistema eléctrico de potencia. Las plantas modernas constan de tres bloques principales: Bloque de generación, Bloque de conversión y  Bloque de evaluación o Interconexión.

- Bloque de generación: Este modulo es encargado de transformar en energía la radiación solar, en este bloque se encuentran los paneles solares los cuales se pueden conectar de distintas formas sea en serie o paralelo.
- Bloque de conversión: Se le conoce como el cerebro de los sistemas fotovoltaicos debido a que son los encargados de transformar la energia bruta proveniente de los paneles en energía util y segura, esta consta de elementos como los inversores lo cuales se encargan de realizar la transformación de corriente continua (CC) a corriente alterna (CA), tambien se puede encontrar los sistemas de protección y seccionamiento como lo son los fusibles, cajas de combinación, diodos de bloqueo y supresores de transitorios (DPS).
- Bloque de evaluación o Interconexión: Es la etapa donde se adecua la energía para su uso final, esta consta de transformadores encargados de elevar el voltaje de baja tension a tensiones industriales y asi reducir perdidas de transporte, tambien estan los puntos de conexión (PCC) encargados de ser el nodo fisico donde el sistema se conecta y acopla a la red eléctrica o a la carga local donde se encuentran los medidores bidireccionales.

#### SCADA industrial.

En la industria moderna se requiere el control, automatización y supervisión de distintos procesos para lograr la mejor eficiencia, reducir altos costos e identificar problemas antes de que escalen, ahi es donde entran los sistemas SCADA industrial que por sus siglas (Supervisory Control and Data Acquisition) son la solución de software y hardware diseñados en especifico para cumplir los requerimientos de supervisión, control y automatización en procesos industriales o infrastructura critica. 

En caso de los sistemas fotovoltaicos es el encargado de garantizar la eficiencia, estabilidad  de la red y el mantenimiento predictivo. El SCADA actua como el núcleo de la tecnología de la operación (OT), centralizando las lecturas criticas del sistema como lo son: potencias (activas/reactivas), tensión, corriente, irradancia de pirometros y temperaturas de celdas, no solo se conecta a la parte de potencia sino que tambien esta conectado a sensores y actuadores necesarios para la supervisión del sistema lo que permite el envío de información y de comandos de control hacia los inversores como puede ser una regulación de rampa de inyección o seleccionamiento de emergencia.

#### Comunicacion Modbus/MQTT.

Dentro del sistema SCADA y la arquitectura híbrida de (OT) se puede encontrar 2 protocolos de comunicación industrial muy fuertes y altamente usados en la industria moderna los cuales son:

- Modbus TCP: Muy usado en redes de área local (LAN) industrial para perimitir la comunicación entre el maestro - esclavo en tiempo real, basicamente la conexión entre el servidor SCADA, los registradores de datos (data loggers) y los inversores o unidades de medición (Sensores y Actuadores).

- MQTT(Message Queuing Telemetry Transport): Es un protocolo ligero altamente usado en la industrial el cual se basa en el modelo publicación-suscripcion, se usa para telemetría IIoT (Internet de las cosas industrial) el cual se encarga de transmitir y transportar los datos historicos del sistema o de la planta hacia las plataformas de supervisión que puede estar alojada en la nube o en centros de control remoto a través de redes WAN.

## 2. Problema de seguridad.

Historicamente el avance en la enegía solar y las tecnologías de la operación (OT) en el sector eléctrico se han enfocado en criterios de desarrollo que priorizan la disponibilidad continua, baja latencia en el control de lazo cerrado y la resilencia ante fallas físicas o ambientales.

Debido a este enfoque los dispositivos de campo como pueden ser los inversores centrales, los controladores lógico programables (PLC) y las unidades de terminal remota (RTU) en los sistemas fotovoltaicos no estan diseñado para afrontar ciberataques. La arquitectura del hardware se optimizó para ejecutar tareas críticas de tiempo real como algoritmos MPPT o sincronización de fase y PLL, lo que conyeva a una capacidad de procesamiento y memoria muy limitada y restringida. Por lo cual la implementación de capas de seguridad preimetral y criptográfica se omitio intencionalmente.

Ademas la implementación de protocolos de comunicación como Modbus TCP o MQTT implican una problematica de ciberseguridad debido la ausencia de diseño de seguridad. El protocolo Modbus TCP el cual opera predominantemente en la capa de control de red local trasnmite toda la carga por texto plano lo cual carece de mecanismos nativos de seguridad como el cifrado y la autentificación fuerte lo cual conyeva al atacante poder realizar técnicas de sniffing de red e interceptar distintos registros de sujección, tambien permite que cualquier dispositivo que se conecte al nodo de red pueda y tenga permisos para enviar algún código de control o código de función Modbus y que se procese por el inversor.

Por otro lado en le protocolo MQTT permite la implementación de seguridad TLS, esta suele prescindirse de cifrado por la carga computacional lo que facilita a vectores de ataques que se basan en suplantación de identidad (spoofing) y la manipulación de datos de telemetría mediante intermediarios comprometidos (Man-In-The-Middle). 

## 3. Amenazas de seguridad.

Dentro de las amenazas de seguridad encontramos:

- Denegación de servicios (DoS/DDoS): Los ataques de Denegación de Servicio (DoS) y Denegación de Servicio Distribuida (DDoS) en entornos FV tienen el objetivo de saturar los recursos de procesamiento en los dispositivos y así lograr ataques de inundación que provoquen un colapso de las interfaces de red en elementos como inversores y data loggers los cuales cuentan con pilas internas de datos limitadas.
- Man-in-the-Middle (MitM): El atacante puede actuar como un intermediario y asi pueda espiar entre la telemetría y alterar los paquetes de datos en tránsito antes de llegar al destino final.
- Ataques a la integridad de datos (DIA): Alteración de datos en tránsito para inducir decisiones erróneas. Se subclasifica en:
    - FDIA (False Data Injection): El atacante puede inyectar mediciones falsas para engañar algoritmos de estimación/control entre esas se puede modificar datos como la irradiancia de los pirómetros o la temperatura del inversor ocacionando que estos reciban esos datos y actuen de manera erronea.
    - Covert Attacks (CA): Los atacantes poseen un conocimiento alto profundo de modelos matematicos del sistema y asi mismo modelo fisico de la planta, con esta información alteran datos de forma gradual y sigilosa anulando a los detectores de anomalias convencionales que dectectan intrusiones y con eso hacer parecer al sistama que el cambio de datos son reales con el objetivo de reducir drasticamente la vida ultil de los componentes o que actuen de manera erronea.
    - Replay Attacks (RA): Captura y retransmisión diferida de tramas legítimas para ejecutar comandos fuera de contexto o activar actuadores indebidamente, el atacante puede grabar tramas de Modbus TCP correspondientes a el funcionamiento nominal óptimo de la planta y posteriormente inyectar dichos datos en otros horarios donde los datos son diferentes para alterar el comportamiento del sistema.
- Exfiltración de datos: Extracción silenciosa de datos operativos, propiedad intelectual o configuraciones sensibles. El honeypot actúa como trampa para capturar TTPs (Tactics, Techniques, Procedures) del atacante.

## 4. Consecuencia industrial.



## 5. Problema final.