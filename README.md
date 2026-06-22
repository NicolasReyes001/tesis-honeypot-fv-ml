# Honeypot para Sistemas Fotovoltaicos con Detección por Machine Learning

Proyecto de grado — Ingeniería Electrónica, Universidad Santo Tomás  
Semestre 8–9 | Proyecto de Grado I y II

---

## Descripción general

Este repositorio contiene el diseño, implementación y documentación de un sistema de seguridad ciberfísica orientado a infraestructuras de generación solar fotovoltaica. El sistema combina tres componentes principales:

- **Honeypot de media interacción** desplegado sobre una Raspberry Pi 4, que expone servicios señuelo SSH, HTTP, Modbus TCP y MQTT para capturar actividad maliciosa dirigida a entornos fotovoltaicos simulados.
- **Módulo de simulación fotovoltaica** que genera telemetría continua y físicamente coherente a partir del modelo de un diodo del generador FV, publicada mediante MQTT y Modbus TCP para dotar al honeypot de credibilidad operativa.
- **Clasificador Random Forest** entrenado sobre los eventos capturados, capaz de clasificar cada sesión en una de siete categorías de tráfico predefinidas.

El proyecto no protege plantas reales ni opera en producción. Su propósito es generar evidencia empírica sobre la viabilidad técnica de detectar intrusiones en infraestructuras fotovoltaicas mediante un entorno de emulación ciberfísico controlado.

---

## Estructura del repositorio

```
tesis-honeypot-fv-ml/
├── docs/                    # Toda la documentación del proyecto
│   ├── anteproyecto/        # Problema, preguntas de investigación, alcance
│   ├── estado_del_arte/     # Revisión de literatura: honeypots, ataques, ML
│   ├── metodologia/         # Arquitectura, protocolos, diseño del dataset
│   ├── resultados/          # Métricas, análisis y discusión de resultados
│   ├── presentaciones/      # Diapositivas de avance y sustentación
│   ├── plan_estrategico/    # Cronograma semanal del proyecto
│   └── final/               # Documento de tesis consolidado
├── honeypot/                # Configuración y scripts del honeypot
│   ├── cowrie/              # Configuración del honeypot SSH (Cowrie)
│   ├── modbus/              # Servidor Modbus TCP señuelo (PyModbus)
│   ├── mqtt/                # Broker MQTT señuelo (Mosquitto)
│   ├── capturas/            # Archivos PCAP y logs raw capturados
│   └── configuraciones/     # docker-compose y archivos de configuración
├── simulacion_fv/           # Módulo de simulación de planta fotovoltaica
│   ├── inversor_modbus/     # Modelo eléctrico del inversor y servidor Modbus
│   ├── mqtt_gateway/        # Publicador MQTT de telemetría FV
│   ├── datasets_irradiancia/ # Datos históricos de irradiancia (NASA POWER)
│   └── pruebas/             # Scripts de validación de la simulación
├── datos/                   # Pipeline de datos del proyecto
│   ├── raw/                 # Eventos sin procesar exportados desde el honeypot
│   ├── procesados/          # Eventos con features extraídas (CSV estructurado)
│   ├── etiquetados/         # Dataset final con etiquetas de clase
│   └── externos/            # Datasets públicos de referencia (UNSW-NB15, etc.)
├── ml/                      # Módulo de machine learning
│   ├── notebooks/           # Notebooks de exploración y entrenamiento
│   ├── preprocessing/       # Scripts de limpieza e ingeniería de features
│   ├── modelos/             # Modelos entrenados serializados (.pkl)
│   ├── evaluacion/          # Métricas, matrices de confusión, curvas ROC
│   └── scripts/             # Scripts de entrenamiento e inferencia
├── dashboard/               # Panel de visualización
│   ├── grafana/             # Dashboards Grafana (fase avanzada)
│   ├── streamlit/           # Aplicación Streamlit (fase inicial)
│   └── imagenes/            # Capturas del dashboard para el documento
├── tesis/                   # Documento formal de tesis
│   ├── latex/               # Fuentes LaTeX del documento
│   ├── figuras/             # Figuras e imágenes para el documento
│   ├── tablas/              # Tablas exportadas para el documento
│   └── pdf/                 # PDFs generados
├── recursos/                # Recursos compartidos del proyecto
│   └── diagramas/           # Diagramas de arquitectura (.mmd, .svg, .png)
├── referencias/             # Gestión de referencias bibliográficas
│   ├── papers/              # PDFs de artículos revisados
│   ├── normas/              # Normas y estándares consultados
│   └── bibliografia.bib     # Archivo BibTeX con todas las referencias
└── docker-compose.yml       # Orquestación de contenedores del sistema
```

---

## Clases del clasificador

El modelo clasifica cada evento capturado en una de siete categorías:

| Clase | Etiqueta                     | Descripción                                                                                   |
| ----- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| 0     | Normal                       | Tráfico legítimo sin indicios de actividad maliciosa                                          |
| 1     | Escaneo                      | Exploración de puertos o descubrimiento de servicios                                          |
| 2     | Fuerza bruta / Intrusión SSH | Intentos repetidos de autenticación SSH y sesiones con actividad maliciosa post-acceso        |
| 3     | Manipulación Modbus/MQTT     | Acceso no autorizado a registros Modbus TCP o tópicos MQTT, incluyendo evidencia de MITM      |
| 4     | DoS/DDoS                     | Inundación de conexiones para saturar un servicio disponible                                  |
| 5     | Replay Attack                | Reenvío diferido de tramas legítimas para forzar acciones no autorizadas                      |
| 6     | FDIA                         | Modificación maliciosa de variables físicas en Modbus o MQTT para inducir decisiones erróneas |

---

## Servicios señuelo expuestos

| Servicio   | Puerto | Herramienta           | Qué captura                                         |
| ---------- | ------ | --------------------- | --------------------------------------------------- |
| SSH        | 22     | Cowrie                | Credenciales, comandos, duración de sesión          |
| HTTP       | 80     | Servidor web señuelo  | Rutas accedidas, métodos HTTP, user-agents          |
| Modbus TCP | 502    | PyModbus señuelo      | Códigos de función, registros accedidos, frecuencia |
| MQTT       | 1883   | Mosquitto con logging | Tópicos, payloads, tipo de operación (pub/sub)      |

---

## Hardware y stack tecnológico

| Componente     | Tecnología                   |
| -------------- | ---------------------------- |
| Plataforma     | Raspberry Pi 4 (4 GB RAM)    |
| Contenedores   | Docker + Docker Compose      |
| Honeypot SSH   | Cowrie                       |
| Simulación FV  | Python (PyModbus, paho-mqtt) |
| Base de datos  | SQLite → PostgreSQL          |
| ML             | scikit-learn (Random Forest) |
| Dashboard      | Streamlit → Grafana          |
| Captura de red | tcpdump (PCAP)               |

---

## Hipótesis de trabajo

**H1 — Credibilidad del señuelo:** La telemetría generada por el modelo físico-matemático presentará coherencia con el comportamiento esperado de una planta FV real, con una desviación menor al 5% respecto a los valores del modelo teórico bajo las mismas condiciones de irradiancia.

**H2 — Desempeño del clasificador:** El clasificador Random Forest alcanzará una precisión, recall y F1-score superiores al 90% en la clasificación de las siete clases definidas sobre el conjunto de prueba independiente.

**H3 — Suficiencia del dataset:** El honeypot permitirá construir un dataset con al menos 500 eventos etiquetados por clase y menos del 5% de registros incompletos.

---

## Estado del proyecto

| Componente                        | Estado      |
| --------------------------------- | ----------- |
| Definición del problema y alcance | Completo    |
| Estado del arte                   | Completo    |
| Diseño de arquitectura            | Completo    |
| Diseño del dataset                | Completo    |
| Implementación del honeypot       | En progreso |
| Módulo de simulación FV           | Pendiente   |
| Entrenamiento del clasificador    | Pendiente   |
| Dashboard                         | Pendiente   |
| Documento de tesis                | En progreso |

---

## Autor

Estudiante de Ingeniería Electrónica — Universidad Santo Tomás  
Proyecto de Grado I y II — Semestres 8 y 9