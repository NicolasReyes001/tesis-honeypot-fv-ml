# dashboard/ — Panel de visualización

Este módulo contiene la implementación del panel de visualización unificado del sistema. Su función es presentar en tiempo casi real las alertas de intrusión clasificadas por el modelo de ML y la telemetría activa de la planta fotovoltaica simulada, permitiendo monitorear el comportamiento del honeypot durante la fase experimental.

---

## Estructura

```
dashboard/
├── streamlit/     # Aplicación Streamlit — fase inicial (prototipo)
├── grafana/       # Dashboards Grafana — fase avanzada (integración)
└── imagenes/      # Capturas del dashboard para el documento de tesis
```

---

## Fases de implementación

### Fase 1 — Streamlit (`streamlit/`)
Prototipo funcional implementado en Python con Streamlit. Se despliega directamente en la Raspberry Pi 4 junto al honeypot. Muestra:

- **Panel de alertas:** tabla de eventos recientes con clase asignada, IP de origen, protocolo, puerto y timestamp. Las clases de mayor severidad (DoS, FDIA, Replay) se destacan visualmente.
- **Telemetría FV en vivo:** gráficas de voltaje DC, corriente DC, potencia AC e irradiancia actualizadas cada 5 segundos a partir de los datos publicados por el módulo de simulación.
- **Resumen estadístico:** distribución de clases detectadas en las últimas 24 horas, total de eventos por protocolo y tasa de eventos por hora.

```bash
# Ejecutar el dashboard Streamlit
streamlit run dashboard/streamlit/app.py
```

### Fase 2 — Grafana (`grafana/`)
Integración con Grafana para visualización avanzada conectada directamente a PostgreSQL. Permite:
- Dashboards persistentes con histórico completo de eventos.
- Alertas configurables por umbral (por ejemplo, más de 50 intentos SSH en 1 minuto).
- Visualización simultánea de telemetría FV y eventos de seguridad en el mismo panel temporal.

---

## Clases visualizadas

El dashboard muestra la clasificación en las mismas siete clases del modelo:

| Clase | Etiqueta                     | Color en dashboard |
| ----- | ---------------------------- | ------------------ |
| 0     | Normal                       | Verde              |
| 1     | Escaneo                      | Azul               |
| 2     | Fuerza bruta / Intrusión SSH | Amarillo           |
| 3     | Manipulación Modbus/MQTT     | Naranja            |
| 4     | DoS/DDoS                     | Rojo               |
| 5     | Replay Attack                | Rojo oscuro        |
| 6     | FDIA                         | Rojo oscuro        |

---

## Limitaciones del dashboard

El sistema **no emite contramedidas activas**. No bloquea IPs, no modifica reglas de firewall ni toma ninguna acción sobre la red en respuesta a las alertas generadas. Su función es exclusivamente de monitoreo y visualización para la fase experimental del proyecto.

---

## Capturas para el documento de tesis

La carpeta `imagenes/` almacena capturas de pantalla del dashboard en operación, usadas como evidencia visual en el capítulo de resultados del documento de tesis. Las capturas deben incluir:
- Panel de alertas con al menos un evento de cada clase.
- Gráfica de telemetría FV durante un período de ataque DoS visible.
- Vista de resumen estadístico con distribución de clases del dataset capturado.