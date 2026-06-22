# recursos/ — Recursos compartidos del proyecto

Esta carpeta almacena recursos gráficos y visuales que son usados en múltiples partes del proyecto: en el documento de tesis, en presentaciones, en el README del repositorio y en los documentos de metodología.

---

## Estructura

```
recursos/
├── diagramas/    # Diagramas de arquitectura y flujos del sistema
├── logos/        # Logos institucionales (universidad, facultad)
└── capturas/     # Capturas de pantalla del sistema en operación
```

---

## `diagramas/`

Contiene los diagramas de arquitectura del sistema en sus distintos formatos:

| Archivo                    | Descripción                                                              | Formato |
| -------------------------- | ------------------------------------------------------------------------ | ------- |
| `arquitectura_sistema.mmd` | Diagrama Mermaid del pipeline completo del sistema (8 capas funcionales) | `.mmd`  |
| `arquitectura_sistema.svg` | Versión exportada del diagrama Mermaid en SVG para el documento          | `.svg`  |
| `arquitectura_sistema.png` | Versión rasterizada para presentaciones                                  | `.png`  |
| `flujo_datos.mmd`          | Diagrama de flujo de datos desde captura hasta clasificación             | `.mmd`  |
| `clases_dataset.png`       | Diagrama visual de las 7 clases del clasificador con ejemplos            | `.png`  |

Los archivos `.mmd` se editan en VS Code con la extensión Mermaid Preview o se renderizan con la CLI de Mermaid:

```bash
# Exportar diagrama Mermaid a PNG
mmdc -i recursos/diagramas/arquitectura_sistema.mmd -o recursos/diagramas/arquitectura_sistema.png

# Exportar a SVG
mmdc -i recursos/diagramas/arquitectura_sistema.mmd -o recursos/diagramas/arquitectura_sistema.svg
```

---

## `capturas/`

Capturas de pantalla del sistema en operación usadas en el documento de tesis y en presentaciones. Deben tener resolución mínima de 1920×1080 px y guardarse en PNG sin compresión.

Capturas esperadas durante la fase experimental:
- Terminal de Cowrie recibiendo una sesión de fuerza bruta SSH.
- Servidor Modbus recibiendo escrituras no autorizadas.
- Dashboard Streamlit con alertas de las 7 clases visibles.
- Matriz de confusión del clasificador.
- Gráfica de importancia de variables del Random Forest.

---

## `logos/`

Logos en alta resolución para portadas y presentaciones:
- Logo Universidad Santo Tomás (versión institucional oficial).
- Logo de la Facultad de Ingeniería Electrónica.

Los logos deben usarse únicamente en la versión y colores oficiales aprobados por la institución.