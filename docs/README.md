# docs/ — Documentación del proyecto

Esta carpeta contiene toda la documentación escrita del proyecto, organizada por etapa y propósito. Cada subcarpeta corresponde a una sección diferente del trabajo de grado.

---

## Estructura

```
docs/
├── anteproyecto/        # Documentos fundacionales del proyecto
├── estado_del_arte/     # Revisión sistemática de literatura científica
├── metodologia/         # Diseño técnico del sistema
├── resultados/          # Análisis y discusión de resultados experimentales
├── presentaciones/      # Diapositivas de avance y sustentación final
├── plan_estrategico/    # Cronograma y rúbrica semanal
└── final/               # Documento consolidado de tesis (versión final)
```

---

## Contenido por carpeta

### `anteproyecto/`
Documentos que definen el problema, el alcance y las preguntas de investigación. Son los documentos fundacionales: todo lo que se construya después debe ser coherente con lo que aquí se establece.

- `problema_definido.md` — Contexto de las plantas FV, vulnerabilidades de Modbus TCP y MQTT, consecuencias industriales y definición formal del problema.
- `preguntas_investigacion.md` — Pregunta general, preguntas específicas, hipótesis de trabajo y matriz de variables del sistema.
- `alcance_sistema.md` — Qué sí y qué no hace el sistema, límites de cada componente y tabla de alcance por módulo.

### `estado_del_arte/`
Revisión crítica de la literatura científica y técnica relevante para el proyecto. Cada documento aborda una línea temática distinta.

- `honeypots_industriales.md` — Análisis de honeypots aplicados a ICS/SCADA: Conpot, Cowrie en entornos OT, datasets Modbus y honeypots MQTT.
- `scada_fotovoltaico.md` — Evidencia de ataques reales a infraestructura solar (SUN:DOWN, SolarView, Stuxnet en contexto energético).
- `ataques_ics.md` — Análisis técnico de MITM, FDIA y Replay Attacks sobre Modbus TCP y MQTT: mecanismos, evidencia en tráfico y consecuencias.
- `ml_para_ids.md` — Comparación de IDS basados en firmas vs. ML. Tipos de aprendizaje aplicables. Análisis de Random Forest, SVM, KNN e Isolation Forest.
- `comparacion_algoritmos.md` — Comparación técnica cuantitativa de los cuatro algoritmos con criterios de métricas, overfitting, escalabilidad e interpretabilidad. Justificación formal de Random Forest como clasificador principal.

### `metodologia/`
Documentos que describen el diseño técnico del sistema: cómo funciona cada componente, qué captura, qué genera y cómo se relacionan entre sí.

- `arquitectura_sistema.md` — Descripción de los ocho módulos del pipeline, flujo de información, componentes por capa y diagrama Mermaid de la arquitectura.
- `protocolos_industriales.md` — Descripción técnica de Modbus TCP y MQTT: estructura de tramas, tipos de registros, modelo cliente-servidor y relevancia en entornos FV.
- `honeypot_cowrie.md` — Estudio de Cowrie: clasificación de honeypots, funcionamiento, configuración, logs generados y cobertura de clases del dataset.
- `diseno_dataset.md` — Definición formal de las siete clases, variables del dataset por protocolo, esquema de la base de datos y estrategia de etiquetado.

### `resultados/`
Se completará durante la fase experimental (Semanas 5–8). Contendrá:
- Métricas de desempeño del clasificador (accuracy, precision, recall, F1-score por clase).
- Matriz de confusión y curvas ROC.
- Análisis de importancia de variables.
- Discusión de resultados y comparación con hipótesis planteadas.

### `presentaciones/`
Diapositivas para entregas de avance ante el director y para la sustentación final ante el jurado.

### `plan_estrategico/`
- `Plan_estrategico.md` — Cronograma de 8 semanas con objetivos diarios, entregables y rúbrica de evaluación semanal (0–100 puntos).

### `final/`
Versión consolidada y revisada del documento de tesis, lista para entrega formal a la universidad.

---

## Convención de nombres de archivos

Los archivos usan `snake_case` en minúsculas sin prefijos de día ni semana. Los prefijos `dia1_`, `dia2_` fueron eliminados en la reorganización del repositorio. El nombre del archivo debe describir el contenido, no cuándo fue escrito.

---

## Clases del dataset (referencia rápida)

Todos los documentos de esta carpeta deben usar esta definición oficial:

| Clase | Etiqueta                     |
| ----- | ---------------------------- |
| 0     | Normal                       |
| 1     | Escaneo                      |
| 2     | Fuerza bruta / Intrusión SSH |
| 3     | Manipulación Modbus/MQTT     |
| 4     | DoS/DDoS                     |
| 5     | Replay Attack                |
| 6     | FDIA                         |