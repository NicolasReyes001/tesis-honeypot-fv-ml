# UNSW-NB15 Dataset

**BibTeX:** `unsw_nb15`  
**Uso en el proyecto:** Complementar las clases 5 (Replay Attack) y 6 (FDIA) del dataset si la captura experimental propia no genera suficientes muestras.

## Descarga
URL: https://research.unsw.edu.au/projects/unsw-nb15-dataset  
Requiere formulario de registro gratuito en la web de UNSW Canberra.

## Archivos a descargar
- `UNSW-NB15_1.csv` a `UNSW-NB15_4.csv` — dataset completo dividido en 4 partes
- `UNSW-NB15_features.csv` — descripción de las 49 features
- `UNSW-NB15_GT.csv` — ground truth labels

## Clases relevantes para el proyecto
Del conjunto de categorías de UNSW-NB15, son relevantes:
- **Backdoor** → mapear a Clase 2 (Intrusión SSH post-acceso)
- **DoS** → mapear a Clase 4 (DoS/DDoS)
- **Fuzzers** → mapear a Clase 1 (Escaneo)
- **Reconocimiento** → mapear a Clase 1 (Escaneo)

Para las clases 5 y 6 (Replay y FDIA), el complemento con UNSW-NB15 es parcial ya que ese dataset no contempla ataques específicos sobre Modbus/MQTT. Se recomienda generar muestras sintéticas controladas en laboratorio.

## Cita
Moustafa, N., & Slay, J. (2015). UNSW-NB15: a comprehensive data set for network intrusion detection systems. *2015 Military Communications and Information Systems Conference (MilCIS)*. IEEE.
