# Cyber-Security Modbus ICS Dataset (Frazão et al., 2019)

**BibTeX:** `frazao2019dataset`  
**DOI:** 10.21227/pjff-1a03  
**Uso en el proyecto:** Dataset de referencia para comparación metodológica y validación del pipeline de clasificación sobre tráfico Modbus.

## Descarga
URL: https://ieee-dataport.org/open-access/cyber-security-modbus-ics-dataset  
Requiere cuenta gratuita en IEEE DataPort.

## Contenido del dataset
- Tráfico Modbus TCP benigno (tráfico normal de un testbed industrial)
- Tráfico Modbus TCP malicioso con ataques DoS
- Capturas PCAP + CSV con features extraídas
- Carpeta con escenario Man-in-the-Middle sobre ARP spoofing

## Relevancia para el proyecto
Este dataset fue generado con la misma metodología que el presente proyecto (honeypot + captura + etiquetado) y respalda la elección de Random Forest como clasificador principal. Los resultados reportados por Frazão et al. con RF sobre este dataset constituyen la referencia de comparación cuantitativa para la sección de resultados de la tesis.

## Cita
Frazão, I., Abreu, P., Cruz, T., Araújo, H., & Simões, P. (2019). Cyber-security Modbus ICS Dataset. IEEE DataPort. DOI: 10.21227/pjff-1a03
