# tesis/ — Documento formal de tesis

Esta carpeta contiene el documento de tesis en su versión formal, escrito en LaTeX conforme a los lineamientos de la Facultad de Ingeniería Electrónica de la Universidad Santo Tomás.

---

## Estructura

```
tesis/
├── latex/      # Fuentes LaTeX del documento (capítulos, portada, bibliografía)
├── figuras/    # Imágenes y figuras incluidas en el documento
├── tablas/     # Tablas exportadas en formato compatible con LaTeX
└── pdf/        # PDFs compilados del documento (versiones de entrega)
```

---

## Estructura del documento

El documento de tesis sigue la estructura estándar requerida por la universidad:

1. **Portada y preliminares** — Título, autor, director, institución, año.
2. **Resumen / Abstract** — Descripción concisa del problema, metodología y resultados principales (máximo 250 palabras, en español e inglés).
3. **Introducción** — Contexto, motivación, planteamiento del problema y estructura del documento.
4. **Estado del arte** — Revisión crítica de literatura sobre honeypots industriales, ciberseguridad FV y ML aplicado a IDS.
5. **Metodología** — Diseño del sistema: honeypot, simulación FV, pipeline de datos y módulo ML.
6. **Implementación** — Descripción técnica de la implementación realizada, decisiones de diseño y dificultades encontradas.
7. **Resultados** — Métricas de desempeño del clasificador, análisis del dataset capturado y validación de hipótesis.
8. **Discusión** — Interpretación de resultados, comparación con trabajos relacionados y limitaciones del sistema.
9. **Conclusiones** — Respuesta a las preguntas de investigación, contribuciones del proyecto y trabajo futuro.
10. **Referencias** — Bibliografía en formato IEEE, generada desde `referencias/bibliografia.bib`.
11. **Anexos** — Configuraciones relevantes, fragmentos de código, tablas de resultados extendidas.

---

## Compilación

```bash
# Desde la carpeta tesis/latex/
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# El PDF final queda en tesis/pdf/
```

---

## Convención de archivos

| Carpeta    | Contenido                                                                        | Formato                |
| ---------- | -------------------------------------------------------------------------------- | ---------------------- |
| `latex/`   | Capítulos, estilos, portada                                                      | `.tex`, `.cls`, `.sty` |
| `figuras/` | Diagramas de arquitectura, capturas del dashboard, gráficas de resultados        | `.png`, `.pdf`, `.svg` |
| `tablas/`  | Tabla comparativa de algoritmos, métricas por clase, características del dataset | `.tex` (tabular)       |
| `pdf/`     | Versiones entregadas al director y al jurado                                     | `.pdf`                 |

---

## Correspondencia con la documentación del proyecto

Los capítulos del documento de tesis se nutren directamente de los documentos en `docs/`:

| Capítulo de tesis | Fuente en docs/                |
| ----------------- | ------------------------------ |
| Estado del arte   | `docs/estado_del_arte/`        |
| Metodología       | `docs/metodologia/`            |
| Resultados        | `docs/resultados/`             |
| Referencias       | `referencias/bibliografia.bib` |

El documento de tesis es la versión formal y revisada de esos documentos de trabajo, adaptada al formato institucional y con el nivel de detalle requerido por el reglamento de trabajos de grado.