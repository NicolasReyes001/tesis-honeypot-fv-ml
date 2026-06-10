# PROYECTO COMO MATERIA UNIVERSITARIA (60 DÍAS)
## Honeypot para Sistemas Fotovoltaicos con Machine Learning

---

# RÚBRICA GENERAL (TODAS LAS SEMANAS)

Cada domingo (0–100 puntos):

- Cumplimiento de objetivos → 25%
- Calidad técnica → 25%
- Documentación → 15%
- Funcionamiento práctico → 20%
- Orden del repositorio → 10%
- Claridad de resultados → 5%

---

# SEMANA 1 — DEFINICIÓN DEL SISTEMA

## Objetivo
Definir completamente el problema, arquitectura y alcance del sistema.

---

## LUNES — Definición del problema real

### Actividades
- Identificar problema en sistemas FV SCADA
- Definir amenazas: FDIA, MITM, replay attacks
- Contextualizar en energía solar real

### Entregable
`docs/semana1/problema_definido.md`

### Revisión diaria
- ¿El problema es real o genérico?
- ¿Tiene contexto industrial?

---

## MARTES — Preguntas de investigación

### Actividades
- Formular 3–5 preguntas de investigación
- Definir hipótesis del sistema
- Relacionar con ciberseguridad industrial

### Entregable
`preguntas_investigacion.md`

### Revisión
- ¿Las preguntas son medibles?
- ¿Son investigables en 60 días?

---

## MIÉRCOLES — Alcance del sistema

### Actividades
- Definir qué SÍ y qué NO hará el sistema
- Delimitar honeypot (SSH + Modbus + MQTT)
- Definir límites del ML

### Entregable
`alcance_sistema.md`

### Revisión
- ¿Está sobredimensionado?
- ¿Es realizable?

---

## JUEVES — Arquitectura del sistema

### Actividades
- Diseñar flujo completo:
  - Planta FV simulada
  - MQTT
  - Modbus
  - Honeypot
  - ML IDS
- Crear diagrama

### Entregable
- `arquitectura.png`
- `arquitectura.md`

### Revisión
- ¿Flujo lógico?
- ¿Hay puntos de captura de ataques?

---

## VIERNES — Protocolos industriales

### Actividades
- Estudiar Modbus TCP
- Estudiar MQTT
- Identificar vulnerabilidades

### Entregable
`protocolos_industriales.md`

### Revisión
- ¿Se entiende cómo fluye la data?

---

## SÁBADO — Cowrie y honeypots

### Actividades
- Analizar Cowrie
- Casos reales de ataques SSH
- Tipos de logs generados

### Entregable
`cowrie_estudio.md`

### Revisión
- ¿Entiendes qué vas a capturar?

---

## DOMINGO — EVALUACIÓN SEMANA 1

### Evaluación
- Claridad del problema
- Coherencia del sistema
- Arquitectura
- Viabilidad

### Resultado
- Nota /100
- Correcciones obligatorias
- Ajustes de arquitectura

---

# SEMANA 2 — ESTADO DEL ARTE

## Objetivo
Construir base científica sólida (papers reales).

---

## LUNES — Honeypots industriales
- Lectura de 3–5 papers
- Resumen técnico

### Entregable
`papers_honeypots.md`

---

## MARTES — SCADA y energía FV
- Ataques reales a plantas solares
- Fallos industriales

### Entregable
`scada_fv.md`

---

## MIÉRCOLES — Ataques industriales
- MITM
- FDIA
- Replay attacks

### Entregable
`ataques_industriales.md`

---

## JUEVES — Machine Learning en IDS
- Random Forest
- SVM
- Detección de anomalías

### Entregable
`ml_ids.md`

---

## VIERNES — Comparación de modelos
- Ventajas y desventajas
- Métricas de evaluación

### Entregable
`comparacion_ml.md`

---

## SÁBADO — Organización bibliográfica
- Zotero / BibTeX
- Matriz de papers

### Entregable
`bibliografia.bib`

---

## DOMINGO — EVALUACIÓN SEMANA 2

### Evaluación
- Calidad de fuentes
- Síntesis
- Coherencia científica

---

# SEMANA 3 — INFRAESTRUCTURA

## Objetivo
Entorno funcional del sistema.

---

## LUNES — Docker base
`docker_test.md`

## MARTES — MQTT broker
`mqtt_setup.md`

## MIÉRCOLES — Node-RED
`nodered_flow.json`

## JUEVES — Cowrie setup
`cowrie_config.md`

## VIERNES — Logging system
`logging_system.md`

## SÁBADO — Integración inicial
`integration_test.md`

---

## DOMINGO — EVALUACIÓN SEMANA 3
- Entorno estable
- Errores técnicos
- Integración parcial

---

# SEMANA 4 — SIMULACIÓN FV

## Objetivo
Planta fotovoltaica simulada funcional.

---

## LUNES — pymodbus
`modbus_intro.md`

## MARTES — variables FV
`fv_variables.md`

## MIÉRCOLES — simulación base
`simulacion_base.py`

## JUEVES — MQTT integración
`mqtt_fv.py`

## VIERNES — dashboard Node-RED
`dashboard_flow.json`

## SÁBADO — pruebas sistema
`test_fv_system.md`

---

## DOMINGO — EVALUACIÓN SEMANA 4
- Realismo de simulación
- Estabilidad de datos

---

# SEMANA 5 — HONEYPOT

## Objetivo
Sistema de captura de ataques funcional.

---

## LUNES — despliegue Cowrie
`cowrie_deploy.md`

## MARTES — ataques SSH
`logs_ssh`

## MIÉRCOLES — Modbus expuesto
`modbus_honeypot.md`

## JUEVES — logging centralizado
`logs_db.py`

## VIERNES — base de datos
SQLite / PostgreSQL

## SÁBADO — pruebas ataques
Dataset inicial

---

## DOMINGO — EVALUACIÓN SEMANA 5
- Honeypot funcional
- Calidad de logs

---

# SEMANA 6 — DATASET

## Objetivo
Dataset propio de ataques.

---

- Ataques SSH
- Nmap scanning
- Modbus fuzzing
- Etiquetado
- Limpieza de datos

### Entregable
Dataset final

---

## DOMINGO — EVALUACIÓN SEMANA 6
- Calidad del dataset
- Etiquetado correcto

---

# SEMANA 7 — MACHINE LEARNING

## Objetivo
IDS funcional.

---

- Preprocessing
- Feature engineering
- Random Forest
- Métricas
- Interpretación

### Entregable
`modelo.pkl` + notebook

---

## DOMINGO — EVALUACIÓN SEMANA 7
- Accuracy
- Overfitting
- Interpretabilidad

---

# SEMANA 8 — INTEGRACIÓN FINAL

## Objetivo
Sistema completo end-to-end.

---

- Dashboard
- Integración ML + logs
- Pruebas finales

### Entregable
Sistema completo

---

## DOMINGO — EVALUACIÓN SEMANA 8
- Sistema end-to-end
- Estabilidad
- Demo funcional

---

# SEMANA 9 — FINAL

## Objetivo
Tesis + defensa.

---

- Redacción final
- Metodología
- Resultados
- Presentación

### Entregable
- Tesis
- Slides

---

## DOMINGO FINAL

- Simulación de defensa real
- Nota final global
- Recomendaciones

---

