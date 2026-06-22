# honeypot/ — Sistema honeypot de media interacción

Este módulo contiene la configuración, scripts y capturas del honeypot desplegado sobre la Raspberry Pi 4. Su función es exponer servicios señuelo que emulan el entorno de comunicación de una planta fotovoltaica real, registrar cada interacción como un evento estructurado y persistir esos eventos en la base de datos para su posterior clasificación.

---

## Estructura

```
honeypot/
├── cowrie/              # Honeypot SSH — configuración de Cowrie
├── modbus/              # Servidor Modbus TCP señuelo (PyModbus)
├── mqtt/                # Broker MQTT señuelo (Mosquitto)
├── capturas/            # Archivos PCAP y logs raw generados
└── configuraciones/     # docker-compose.yml y archivos de entorno
```

---

## Servicios señuelo

### SSH — Puerto 22 (`cowrie/`)
Herramienta: **Cowrie**

Emula un servidor SSH de un sistema de monitoreo fotovoltaico. Acepta conexiones con credenciales configuradas y presenta al atacante un entorno de shell simulado. Registra en formato JSON:
- Dirección IP de origen y timestamp de cada intento
- Credenciales utilizadas (usuario + contraseña)
- Comandos ejecutados durante la sesión
- Duración total de la sesión
- Archivos descargados (si los hay)

Cubre las clases **1 (Escaneo)** y **2 (Fuerza bruta / Intrusión SSH)** del dataset.

### Modbus TCP — Puerto 502 (`modbus/`)
Herramienta: **PyModbus** (servidor señuelo personalizado)

Emula un inversor solar SMA con registros holding mapeados a variables físicas de la planta fotovoltaica simulada. Recibe las lecturas del módulo de simulación FV y las expone como registros Modbus reales. Registra:
- Código de función Modbus utilizado (lectura, escritura, diagnóstico)
- Dirección inicial y número de registros accedidos
- Tipo de operación (lectura vs. escritura)
- Frecuencia de acceso (solicitudes por unidad de tiempo)
- IP de origen y timestamp

Cubre las clases **3 (Manipulación Modbus/MQTT)**, **4 (DoS/DDoS)**, **5 (Replay Attack)** y **6 (FDIA)** del dataset.

### MQTT — Puerto 1883 (`mqtt/`)
Herramienta: **Mosquitto** con plugin de logging

Broker MQTT que recibe la telemetría publicada por el módulo de simulación FV y la expone a cualquier cliente que se conecte a la red del laboratorio. Registra:
- Tópico de publicación o suscripción
- Tamaño del payload en bytes
- Tipo de operación (PUBLISH vs. SUBSCRIBE)
- Frecuencia de publicación
- IP de origen y timestamp

Cubre las clases **3 (Manipulación Modbus/MQTT)**, **4 (DoS/DDoS)**, **5 (Replay Attack)** y **6 (FDIA)** del dataset.

### Captura de red general (`capturas/`)
Herramienta: **tcpdump**

Captura todo el tráfico de red en formato PCAP de forma complementaria a los logs de cada servicio. Los archivos PCAP son procesados por scripts Python en `datos/` para extraer features de flujo (duración, bytes totales, paquetes, flags TCP, tasa de paquetes). Cubre los patrones de tráfico de todas las clases.

---

## Flujo de datos

```
Interacción externa
        ↓
┌─────────────────────────────────────┐
│  Servicios señuelo (Docker)         │
│  SSH:22  HTTP:80  Modbus:502  MQTT:1883 │
└─────────────────────────────────────┘
        ↓
  Logs JSON + PCAP
        ↓
  Parser Python (datos/raw/ → datos/procesados/)
        ↓
  Base de datos SQLite → PostgreSQL
```

---

## Despliegue

El honeypot se despliega íntegramente mediante Docker Compose sobre la Raspberry Pi 4. Cada servicio corre en un contenedor aislado. Ver `configuraciones/docker-compose.yml` para la configuración completa.

```bash
# Levantar todos los servicios
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Detener
docker compose down
```

---

## Notas de seguridad

El honeypot **no debe conectarse a redes de producción**. Opera únicamente en la red de laboratorio controlada. Ningún servicio expuesto tiene acceso a sistemas reales. Todo el tráfico capturado es para fines de investigación.