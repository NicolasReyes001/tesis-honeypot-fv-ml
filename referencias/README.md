# referencias/ — Gestión de referencias bibliográficas

Esta carpeta centraliza todas las fuentes del proyecto: el archivo BibTeX maestro, los PDFs de los artículos revisados y los documentos de normas y estándares consultados.

---

## Estructura

```
referencias/
├── bibliografia.bib    # Archivo BibTeX maestro con todas las referencias
├── papers/             # PDFs de artículos científicos y reportes técnicos
└── normas/             # PDFs de normas y estándares (IEC, IEEE, ISO, NIST)
```

---

## `bibliografia.bib`

Archivo BibTeX con **32 entradas** organizadas en 8 secciones. Se usa directamente desde LaTeX en `tesis/latex/` con `\bibliography{../../referencias/bibliografia}`.

Las secciones son:
1. Honeypots industriales ICS/SCADA
2. Honeypots MQTT e IIoT
3. Ciberseguridad en sistemas fotovoltaicos
4. Ataques industriales (MITM, FDIA, Replay)
5. Machine Learning para IDS
6. Normas y estándares
7. Libros y referencias generales
8. Fuentes de datos y APIs

---

## `papers/`

PDFs de artículos científicos, reportes técnicos y publicaciones académicas. Los archivos se nombran con el mismo identificador BibTeX para facilitar la trazabilidad.

### Cómo citar desde LaTeX

```latex
\cite{grigoriou2023honeypots}   % Artículo de Future Internet
\cite{radoglou2020modbus}       % Artículo de MOCAST 2020
\cite{frazao2018dos}            % Artículo de CRITIS 2018
```

Ver el catálogo completo de PDFs a descargar en la sección siguiente.

---

## `normas/`

PDFs de normas internacionales y documentos de estándares. Muchas normas IEC e IEEE son de acceso pagado; en ese caso se guarda aquí el documento de acceso público más cercano (borrador público, versión anterior gratuita, o resumen ejecutivo oficial).

---

## Catálogo completo de referencias por carpeta

### `referencias/papers/` — PDFs a descargar

#### Sección 1: Honeypots ICS/SCADA

| Archivo a guardar | Referencia BibTeX | URL de descarga | Acceso |
|-------------------|-------------------|-----------------|--------|
| `grigoriou2023honeypots.pdf` | `grigoriou2023honeypots` | https://www.mdpi.com/1999-5903/15/7/241 → botón "Download PDF" | **Abierto** |
| `lemay2016scada.pdf` | `lemay2016scada` | https://www.usenix.org/system/files/conference/cset16/cset16-paper-lemay.pdf | **Abierto** |
| `radoglou2020modbus.pdf` | `radoglou2020modbus` | https://ieeexplore.ieee.org/document/9200287 → "Full Text PDF" (requiere IEEE Xplore, disponible con cuenta institucional) | Institucional |
| `frazao2018dos.pdf` | `frazao2018dos` | https://doi.org/10.1007/978-3-030-05849-4_19 (Springer, requiere acceso) — alternativa: buscar en ResearchGate con el título exacto | Institucional / ResearchGate |
| `nawrocki2016honeypot.pdf` | `nawrocki2016honeypot` | https://arxiv.org/pdf/1608.06249 | **Abierto** |
| `icssim2022.pdf` | `icssim2022` | https://arxiv.org/pdf/2210.13325 | **Abierto** |

#### Sección 2: Honeypots MQTT e IIoT

| Archivo a guardar | Referencia BibTeX | URL de descarga | Acceso |
|-------------------|-------------------|-----------------|--------|
| `adaptive_mqtt_honeypot2025.pdf` | `adaptive_mqtt_honeypot2025` | https://link.springer.com/chapter/10.1007/978-3-032-13714-2_28 (Springer) — buscar en ResearchGate como alternativa | Institucional / ResearchGate |
| `pirates_mqtt2024.pdf` | `pirates_mqtt2024` | https://www.researchgate.net/publication/384011283 → "Request full-text" o "Download" | ResearchGate |

#### Sección 3: Ciberseguridad en sistemas fotovoltaicos

| Archivo a guardar | Referencia BibTeX | URL de descarga | Acceso |
|-------------------|-------------------|-----------------|--------|
| `forescout_sundown2025.pdf` | `forescout_sundown2025` | https://www.forescout.com/resources/sun-down-research-report/ → formulario de descarga gratuita | **Abierto** (registro) |
| `singla2025dos_inverters.pdf` | `singla2025dos_inverters` | https://ieeexplore.ieee.org/document/10977548 → "Full Text PDF" (IEEE Xplore) | Institucional |

#### Sección 4: Ataques industriales

| Archivo a guardar | Referencia BibTeX | URL de descarga | Acceso |
|-------------------|-------------------|-----------------|--------|
| `liu2009fdia.pdf` | `liu2009fdia` | https://dl.acm.org/doi/10.1145/1653662.1653666 → "PDF" (requiere ACM DL, con cuenta institucional) — alternativa: buscar en Semantic Scholar o Google Scholar | Institucional |
| `rajesh2021replay.pdf` | `rajesh2021replay` | https://doi.org/10.1155/2021/8887666 → Hindawi/Wiley Open Access | **Abierto** |
| `sanchez2017mitm.pdf` | `sanchez2017mitm` | https://www.giac.org/paper/gccc/817/man-in-the-middle-attack-modbus-tcp-illustrated-wireshark/116887 | **Abierto** |

#### Sección 5: Machine Learning para IDS

| Archivo a guardar | Referencia BibTeX | URL de descarga | Acceso |
|-------------------|-------------------|-----------------|--------|
| `liu2008isolation.pdf` | `liu2008isolation` | https://ieeexplore.ieee.org/document/4781136 (IEEE Xplore) — alternativa: buscar "Isolation Forest Liu 2008 pdf" en Google Scholar | Institucional |
| `rf_smote2022.pdf` | `rf_smote2022` | https://link.springer.com/article/10.1186/s13634-022-00871-6 → Open Access, descarga directa | **Abierto** |
| `comparison_rf_svm2024.pdf` | `comparison_rf_svm2024` | https://www.researchgate.net/publication/383162577 | ResearchGate |
| `comparison_svm_rf_ddos2025.pdf` | `comparison_svm_rf_ddos2025` | https://rsisinternational.org/journals/ijriss/articles/comparison-of-the-use-of-support-vector-machine-svm-random-forest-algorithms-rf-for-ddos-attack-detection/ → "Download PDF" | **Abierto** |

#### Sección 6: Libros

| Archivo a guardar | Referencia BibTeX | Nota |
|-------------------|-------------------|------|
| `spitzner2002honeypots_cap1.pdf` | `spitzner2002honeypots` | Libro físico/ebook. Guardar aquí el capítulo 1 o resumen si está disponible. ISBN: 978-0321108951. Disponible en Google Books con preview parcial. |

---

### `referencias/normas/` — Documentos de estándares

| Archivo a guardar | Referencia BibTeX | URL / Nota |
|-------------------|-------------------|------------|
| `nist_ir8498.pdf` | `nist_ir8498` | https://www.nccoe.nist.gov/projects/cybersecurity-smart-inverters-guidelines-residential-and-light-commercial-solar-energy → descarga directa del PDF desde NIST. **Abierto.** |
| `ieee1547_resumen.pdf` | `ieee1547` | https://standards.ieee.org/ieee/1547/7941/ — el estándar completo es de pago. Guardar aquí el resumen ejecutivo público o el documento de acceso abierto relacionado: IEEE Std 1547-2018 overview disponible en IEEE Xplore con cuenta institucional. |
| `iec62443_overview.pdf` | `iec62443` | https://www.iec.ch/cyber-security → documentos de introducción gratuitos en el sitio IEC. El texto completo de la norma es de pago. Guardar el documento de overview público: "IEC 62443 Cybersecurity for OT" disponible en https://webstore.iec.ch (buscar documentos free-to-read). |
| `iso_iec20922_mqtt.pdf` | `iso_iec20922` | La especificación pública del protocolo MQTT 3.1.1 (equivalente técnico de ISO/IEC 20922) está disponible en: http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.pdf → **Abierto.** |
| `modbus_spec.pdf` | `iec61158` | La especificación oficial de Modbus es pública: https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf → **Abierto.** |

---

## Datasets externos

Los datasets públicos no se guardan en `referencias/` sino en `datos/externos/`:

| Dataset | Carpeta destino | URL de descarga |
|---------|-----------------|-----------------|
| UNSW-NB15 | `datos/externos/unsw_nb15/` | https://research.unsw.edu.au/projects/unsw-nb15-dataset → formulario de acceso |
| Cyber-Security Modbus ICS Dataset (Frazão et al.) | `datos/externos/modbus_ics/` | https://ieee-dataport.org/open-access/cyber-security-modbus-ics-dataset (IEEE DataPort, requiere cuenta gratuita) |

---

## Cómo agregar nuevas referencias

1. Añadir la entrada BibTeX en `bibliografia.bib` en la sección correspondiente.
2. Descargar el PDF y guardarlo en `referencias/papers/` o `referencias/normas/` con el nombre del identificador BibTeX.
3. Citar en el documento LaTeX con `\cite{identificador}`.
4. Si la referencia es un dataset externo, registrar la URL en esta sección y guardar los datos en `datos/externos/`.

---

## Acceso institucional

Para los artículos que requieren suscripción, la Universidad Santo Tomás dispone de acceso a bases de datos académicas. Consultar con la biblioteca el acceso a:
- **IEEE Xplore** — para artículos de conferencias IEEE (MOCAST, APEC, ICDM)
- **ACM Digital Library** — para artículos de CCS
- **Springer Link** — para capítulos de Springer (CRITIS)

Alternativamente, muchos de estos artículos están disponibles en **Semantic Scholar** (semanticscholar.org) o **ResearchGate** de forma gratuita.
