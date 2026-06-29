# Ataques industriales: MITM, FDIA y Replay Attacks
**Semana 2 — Día 3**

## 1. Introducción

Los días anteriores de esta semana establecieron, respectivamente, que existe un cuerpo consolidado de investigación sobre honeypots industriales y que la ciberseguridad en infraestructura solar fotovoltaica constituye una amenaza real y documentada. El presente documento profundiza técnicamente en tres de los ataques que conformarán parte de las clases del dataset del proyecto: los ataques Man-in-the-Middle (MITM), los False Data Injection Attacks (FDIA) y los Replay Attacks. A diferencia de un enfoque puramente descriptivo, el objetivo de este análisis es comprender el mecanismo interno de cada ataque, la evidencia técnica que deja en el tráfico de red y los protocolos involucrados, de manera que las futuras etiquetas del clasificador estén fundamentadas en comportamientos observables y no únicamente en nombres extraídos de la literatura.

## 2. Man-in-the-Middle (MITM)

### Definición

Un ataque Man-in-the-Middle ocurre cuando un agente malicioso logra interponerse entre dos entidades legítimas que intercambian información dentro de una red industrial, típicamente entre un sistema SCADA o estación HMI y un dispositivo de campo como un inversor o PLC, interceptando y eventualmente modificando los mensajes transmitidos sin que ninguna de las partes detecte la presencia del intermediario.

### Mecanismo de ejecución

El vector de entrada más documentado para establecer un MITM dentro de una red industrial Ethernet es el ARP spoofing, una técnica en la que el atacante envía mensajes ARP falsificados a la red local, haciendo que su propia dirección MAC quede asociada en las tablas ARP de las víctimas con la dirección IP de un dispositivo legítimo, como el gateway o el PLC objetivo. Al lograr esta asociación falsa, todo el tráfico que las víctimas creen estar enviando al dispositivo legítimo es en realidad redirigido a través de la máquina del atacante, quien puede inspeccionarlo, modificarlo o descartarlo selectivamente antes de reenviarlo a su destino real.

Una vez establecida esta posición, herramientas de manipulación de tráfico como Ettercap permiten al atacante definir filtros que alteran campos específicos de los paquetes en tránsito. Un caso documentado experimentalmente consiste en modificar comandos Modbus TCP dirigidos a activar una bobina (coil) de un PLC: el filtro intercepta el valor hexadecimal `ff00`, que en el protocolo Modbus representa la instrucción de encender la bobina, y lo reemplaza por `0000`, que representa apagarla. La estación maestra no recibe ningún mensaje de error, ya que desde su perspectiva el comando fue transmitido y aceptado normalmente; sin embargo, el dispositivo de campo ejecuta la acción opuesta a la solicitada.

### Evidencia técnica que deja

Como Modbus TCP es un protocolo sin estado, en texto claro y sin ningún mecanismo de validación de integridad, la modificación de un paquete en tránsito no genera ningún error de protocolo detectable por las partes legítimas. La evidencia de un MITM, por tanto, no se encuentra en el contenido del mensaje individual, sino en discrepancias indirectas observables a nivel de red: cambios inesperados en la tabla ARP (una misma dirección MAC asociada a más de una IP, o cambios no justificados en la asociación IP-MAC), latencias anómalas introducidas por el reenvío a través del atacante, o inconsistencias entre el valor reportado por el dispositivo de campo y el valor que efectivamente se esperaría dado el comando enviado.

### Consecuencias industriales

Las consecuencias documentadas incluyen decisiones operativas incorrectas tomadas por el operador con base en información falsa, pérdida de visibilidad real sobre el estado del proceso, alteración silenciosa de parámetros de control, degradación del algoritmo de seguimiento del punto de máxima potencia (MPPT) cuando el ataque se dirige a un inversor fotovoltaico, y afectación de la estabilidad operativa del sistema al ejecutarse acciones opuestas o distintas a las solicitadas.

## 3. False Data Injection Attack (FDIA)

### Definición

Un FDIA consiste en la modificación deliberada de los datos medidos o reportados por los sensores de un sistema, con el objetivo de inducir errores en los algoritmos de estimación de estado o en la toma de decisiones automáticas del SCADA, sin que dicha modificación sea detectada por los mecanismos convencionales de detección de datos erróneos. A diferencia del MITM, cuyo objetivo es controlar el canal de comunicación, el FDIA busca alterar específicamente el significado físico de la información transmitida, de forma que el sistema receptor construya una representación falsa, pero internamente consistente, del estado real del proceso.

### Mecanismo de ejecución

Desde la perspectiva formal empleada en la literatura de sistemas de potencia, un estimador de estado relaciona un vector de mediciones z con un vector de variables de estado x mediante una función h, de forma que z = h(x) + e, donde e representa el error de medición. La construcción clásica de un FDIA consiste en diseñar un vector de ataque a tal que la medición comprometida z_a = z + a produzca una estimación de estado desplazada de forma controlada, sin que el residuo entre la medición y la estimación supere el umbral utilizado por las pruebas estadísticas de detección de datos erróneos, como la prueba de chi-cuadrado o la prueba del mayor residuo normalizado. Para lograr esto, el atacante necesita conocer la matriz de configuración del sistema H (la matriz jacobiana que relaciona linealmente las mediciones con las variables de estado), de manera que pueda construir el vector de ataque como a = Hc, donde c representa el desplazamiento deseado en las variables de estado; al construirse de esta forma, el vector de ataque permanece dentro del espacio de la columna de H y el residuo de la estimación no se altera, por lo que el ataque pasa inadvertido ante las pruebas convencionales de detección de datos erróneos. Esta dependencia del conocimiento de la topología y configuración del sistema es lo que convierte al FDIA en un ataque particularmente sigiloso pero también exigente en términos de información previa: el atacante no solo falsea un valor, sino que lo hace de manera matemáticamente coherente con el modelo físico del sistema, permaneciendo indistinguible del ruido de medición normal solo en la medida en que dicho conocimiento de la matriz H sea preciso.

En el contexto específico de una planta fotovoltaica, este mecanismo se traduce en la publicación o escritura de valores falsificados de variables físicas como la irradiancia solar, la temperatura del panel, la energía acumulada o el voltaje de salida, ya sea a través de registros Modbus TCP comprometidos o mediante la publicación de mensajes falsos en tópicos MQTT legítimos.

### Evidencia técnica que deja

A diferencia del MITM, donde la evidencia es principalmente de red, el FDIA deja evidencia de naturaleza física-estadística: la variable inyectada presenta una desviación abrupta o incoherente respecto a su comportamiento esperado dado el contexto físico del sistema. Por ejemplo, una irradiancia reportada de 1200 W/m² durante la madrugada, o un salto instantáneo de potencia de 100 kW a 350 kW sin una transición gradual coherente con la dinámica de un inversor real, constituyen huellas observables que distinguen al FDIA del ruido de medición legítimo.

### Consecuencias industriales

Entre las consecuencias documentadas se incluyen decisiones de control equivocadas basadas en datos físicamente inconsistentes, pérdida de eficiencia operativa, activación indebida de protecciones del sistema ante condiciones inexistentes, ocultamiento deliberado de fallas reales mediante el enmascaramiento de los valores que las revelarían, y la corrupción de los registros históricos utilizados para análisis posteriores de desempeño de la planta.

## 4. Replay Attacks

### Definición

Un Replay Attack consiste en la captura de mensajes legítimos previamente transmitidos en la red y su retransmisión posterior, fuera de su contexto temporal original, con el fin de que el sistema receptor ejecute nuevamente una acción válida pero indebida en ese nuevo momento. A diferencia del MITM y el FDIA, el Replay Attack no requiere modificar el contenido del mensaje: su peligrosidad reside precisamente en que el mensaje reenviado es, en sí mismo, completamente legítimo y fue generado por una fuente autorizada.

### Mecanismo de ejecución

El atacante primero debe posicionarse en la red para capturar pasivamente el tráfico, frecuentemente mediante la misma técnica de ARP spoofing descrita para el MITM, dado que Modbus TCP y MQTT no cifran su contenido por defecto. Una vez capturado un mensaje de interés, como una orden de cambio de modo de operación o una escritura de configuración crítica, el atacante simplemente retransmite el mismo paquete capturado en un momento posterior. Como el protocolo no incorpora de forma nativa mecanismos de unicidad como números de secuencia o marcas temporales validadas por el receptor, el dispositivo de campo ejecuta la acción nuevamente sin distinguir que se trata de una repetición y no de una instrucción nueva.

La literatura técnica documenta una solución experimental a este problema mediante la incorporación de marcas de tiempo y números de secuencia en las comunicaciones Modbus, acompañada de un módulo de filtrado de tramas. En una implementación reportada, se definió un umbral de 500 milisegundos entre la marca de tiempo del mensaje y el momento de su recepción: los mensajes Modbus cuya diferencia temporal excedía dicho umbral, o cuyo número de secuencia no coincidía con el esperado, eran rechazados por el módulo de filtrado. Esta implementación logró bloquear el 97% de las transacciones Modbus maliciosas simuladas, evidenciando que, si bien el protocolo es vulnerable por diseño, la inconsistencia temporal constituye la huella técnica más confiable para detectar un Replay Attack.

### Evidencia técnica que deja

La principal evidencia observable de un Replay Attack es la reaparición de un payload idéntico o casi idéntico al de una sesión anterior, fuera del ciclo temporal esperado de operación normal del sistema. Esto se traduce en patrones como la repetición de la misma escritura de registro Modbus en horarios atípicos, la publicación de un mensaje MQTT con un payload idéntico a uno ya observado horas o días antes, o la ejecución de un comando de control en un contexto operativo donde dicho comando no tendría justificación lógica (por ejemplo, una orden de limitación de potencia ejecutada durante la noche, cuando la planta ya no está generando).

### Consecuencias industriales

Las consecuencias documentadas incluyen la repetición de comandos críticos de control, cambios inesperados en el estado operativo del sistema, ejecución de acciones fuera del contexto que las justificaba originalmente, y la dificultad inherente de detección que se deriva de tratarse de datos legítimos reutilizados de forma indebida.

## 5. Relación con protocolos industriales

### Modbus TCP

Sobre este protocolo, el MITM puede modificar respuestas de lectura, alterar registros de escritura en tránsito o falsificar el estado reportado del inversor, como en el ejemplo documentado de inversión del valor de una bobina mediante un filtro Ettercap. El FDIA puede falsificar directamente los valores almacenados en los registros holding correspondientes a potencia, voltaje, corriente o alarmas del sistema. El Replay puede reutilizar escrituras válidas previamente capturadas, cambios de configuración o comandos de control, aprovechando la ausencia nativa de números de secuencia o marcas de tiempo verificables en el protocolo estándar.

### MQTT

Sobre MQTT, el MITM puede interceptar y modificar mensajes publicados en tópicos cuando la conexión no utiliza TLS, dado que el protocolo en su configuración base no cifra el contenido de los mensajes. El FDIA puede manifestarse mediante la publicación de un payload falso en un tópico legítimo, por ejemplo fv/inversor/potencia = 500, mientras la potencia real generada es sustancialmente distinta. El Replay puede reenviar publicaciones legítimas previamente capturadas o retenidas (mensajes con la bandera retained activada), forzando que un suscriptor reciba nuevamente una instrucción o un dato de telemetría fuera de su contexto temporal original.

## 6. Relación con el proyecto

Estos tres ataques constituyen el núcleo de las clases más complejas del dataset propuesto, ya que a diferencia del escaneo de puertos o la fuerza bruta SSH, no dejan evidencia directa en forma de credenciales o comandos de shell, sino en patrones más sutiles a nivel de protocolo y de coherencia física de los datos. El honeypot permitirá representar evidencia asociada a estos ataques mediante el registro de escrituras repetidas o anómalas en Modbus TCP, lecturas inconsistentes respecto al comportamiento esperado, publicaciones MQTT con payloads idénticos a sesiones anteriores y abuso de tópicos mediante suscripciones o publicaciones no autorizadas.

## 7. Variables potenciales para Machine Learning

| Variable                  | Ataque relacionado | Descripción                                                                                                                                                 |
| ------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| frecuencia_escrituras     | Replay             | Número de escrituras Modbus/MQTT por unidad de tiempo; picos anómalos sugieren reutilización automatizada de mensajes                                       |
| repeticion_payload        | Replay             | Indicador booleano de coincidencia exacta entre el payload actual y un payload previamente observado en la sesión histórica                                 |
| inconsistencia_fisica     | FDIA               | Medida de discrepancia entre el valor reportado y el rango físicamente esperado dado el contexto (hora del día, temperatura ambiente, generación previa)    |
| salto_anomalo_variable    | FDIA               | Diferencia abrupta entre dos lecturas consecutivas de la misma variable, superior a la tasa de cambio físicamente posible                                   |
| variacion_improbable      | FDIA               | Desviación estadística de la variable respecto a su distribución histórica esperada                                                                         |
| discrepancia_lectura      | MITM               | Diferencia entre el valor reportado por el dispositivo y el valor esperado dado el comando enviado previamente                                              |
| cambios_fuera_horario     | MITM / Replay      | Indicador de que la escritura o comando se ejecutó en un horario atípico respecto al patrón operativo normal de la planta                                   |
| origen_no_habitual        | MITM               | Cambio no justificado en la asociación IP-MAC observada en la tabla ARP de la red del honeypot                                                              |
| delta_timestamp_secuencia | Replay             | Diferencia temporal entre la marca de tiempo del mensaje Modbus y el momento de recepción, contrastada contra el umbral de aceptación (por ejemplo, 500 ms) |

## 8. Conclusiones

El análisis técnico realizado en este documento confirma que MITM, FDIA y Replay no constituyen amenazas independientes entre sí, sino tres manifestaciones distintas de un mismo problema estructural: la ausencia de autenticación, cifrado e integridad criptográfica nativa en los protocolos de comunicación industrial tradicionales como Modbus TCP, y la configuración frecuentemente insegura del protocolo MQTT en entornos IIoT. En sistemas fotovoltaicos modernos, donde estos protocolos conviven y donde la información transmitida tiene un correlato físico directo con la generación de energía, estos ataques adquieren una relevancia particular porque no solo comprometen la confidencialidad de los datos, sino que pueden inducir decisiones erróneas tanto humanas como automáticas con consecuencias físicas reales sobre la planta.

Desde la perspectiva del diseño del dataset, este análisis demuestra que cada uno de los tres ataques deja una huella técnica distinguible: el MITM se evidencia principalmente a nivel de red (anomalías ARP, discrepancias entre comando y respuesta), el FDIA se evidencia a nivel físico-estadístico (incoherencia entre el valor reportado y el comportamiento esperado del proceso), y el Replay se evidencia a nivel temporal (repetición de payloads fuera de su ventana de validez esperada). Esta distinción fundamenta la viabilidad de construir un clasificador capaz de diferenciar estas tres clases a partir de atributos derivados de los logs del honeypot, en lugar de depender de un enfoque genérico de detección de anomalías sin base en el comportamiento específico de cada ataque.

## Referencias

- Rajesh, L., & Satyanarayana, P. (2021). Detection and Blocking of Replay, False Command, and False Access Injection Commands in SCADA Systems with Modbus Protocol. Security and Communication Networks, vol. 2021, Article ID 8887666, 15 páginas. Department of Electronics and Communication Engineering, Koneru Lakshmaiah Education Foundation, India. DOI: 10.1155/2021/8887666
- Sanchez, G. (2017). Man-in-the-Middle Attack Against Modbus TCP Illustrated with Wireshark. SANS Institute / GIAC GCCC Paper. https://www.giac.org/paper/gccc/817/man-in-the-middle-attack-modbus-tcp-illustrated-wireshark/116887
- Liu, Y., Ning, P., & Reiter, M. K. (2009). False Data Injection Attacks Against State Estimation in Electric Power Grids. En Proceedings of the 16th ACM Conference on Computer and Communications Security (CCS '09), Chicago, Illinois, EE. UU., pp. 21–32. DOI: 10.1145/1653662.1653666. Versión extendida: Liu, Y., Ning, P., & Reiter, M. K. (2011). ACM Transactions on Information and System Security (TISSEC), 14(1), Artículo 13, 33 páginas. DOI: 10.1145/1952982.1952995
- ICSSIM: A Framework for Building Industrial Control Systems Security Simulation Testbeds (2022). arXiv preprint. https://arxiv.org/pdf/2210.13325
- Armis Research. ModiPwn — ARP Spoofing and Man-in-the-Middle Attacks Against Modicon PLCs. https://www.armis.com/research/modipwn/
- MITRE. ATT&CK for ICS — Technique T830: Man in the Middle. https://collaborate.mitre.org/attackics/index.php/Technique/T830
