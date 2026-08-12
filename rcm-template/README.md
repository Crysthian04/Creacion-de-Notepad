# Generador de plantillas RCM2 / MSG-3

Repositorio Python que **compila** un libro Excel habilitado para macros (`.xlsm`)
listo para conducir un análisis RCM completo sobre **una máquina individual** y
exportar el plan de mantenimiento resultante a cualquier CMMS mediante
adaptadores intercambiables.

El motor de decisión es **RCM2 (SAE JA1011 / JA1012)**; la documentación de
salida sigue la convención **MSG-3**; la taxonomía base es **ISO 14224**, por ser
la que comparten SAP PM e IBM Maximo.

> El libro no se edita a mano y no se versiona: se compila. La fuente de verdad
> son este repositorio y la carpeta `seed/`.

## Estado

**Fases 1 a 3 de 10 completadas.**

| Fase | Entregable | Estado |
|---|---|---|
| 1 | Pipeline de compilación, `.xlsm` con VBA importado y firmado | Listo |
| 2 | `Parametros`, `Diccionario`, catálogos, librerías, carga desde `seed/` | Listo |
| 3 | `Contexto Operacional`, `Criticidad del Activo`, `Particion`, `AMFE` | Listo |
| 4 | `Arbol de Decision` + `modDecisionEngine` | Pendiente |
| 5 | `Lista de Tareas` + `modTextBuilder` + `modValidate` + `Calidad del Plan` | Pendiente |
| 6 | `modPackaging` + `Empaquetado` + `Plan de Mantenimiento` + `Materiales` | Pendiente |
| 7 | Adaptadores SAP PM y Maximo + `modExport` + golden files | Pendiente |
| 8 | `Plan Previo` + `modImportGap` + `Gap List` + `Resumen` | Pendiente |
| 9 | `modUI`, roles, `modChangeControl`, `INICIO`, protección | Pendiente |
| 10 | Documentación, manual de usuario, pruebas completas, versión 1.0 | Pendiente |

El libro que se compila hoy tiene 11 hojas y no lleva macros funcionales todavía:
el único módulo VBA es la prueba de humo que valida el pipeline.

## Requisitos

- Python 3.11 o superior.
- Para producir el `.xlsm` con macros: **Windows con Excel de escritorio** y la
  opción *Confiar en el acceso al modelo de objetos de proyectos de VBA*
  habilitada en el Centro de confianza. Sin ella, la importación de módulos falla
  con el error 1004; el build lo detecta antes de abrir Excel y muestra la ruta
  exacta del ajuste.

En Linux o macOS el build funciona igual, pero omite la etapa de Excel y entrega
un `.xlsx` **sin macros**: sirve para revisar estructura y fórmulas, no como
entregable. Los detalles están en [`docs/entorno-build.md`](docs/entorno-build.md).

## Instalación

```bash
pip install -r requirements.txt        # uso
pip install -r requirements-dev.txt    # desarrollo y pruebas
```

## Compilar

```bash
python build/build.py
python build/build.py --output dist/RCM_Template_v0.1.0.xlsm --sign
python build/build.py --no-com         # solo estructura, sin Excel
```

Cada compilación escribe `dist/manifest.json` con la versión, la fecha, los
hashes de los módulos VBA y el estado de la firma.

## Pruebas

```bash
python -m pytest tests -q
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `build/` | Orquestador, capa COM, comprobación previa del entorno y firma. |
| `src/sheets/` | Un constructor `openpyxl` por hoja. `REGISTRY` fija el orden de las pestañas. |
| `src/common/` | Configuración, estilos, nombres definidos, validaciones. |
| `src/seedloader/` | Carga de `seed/` a las hojas. |
| `vba/` | Módulos VBA versionados como texto (`.bas` / `.cls` / `.frm`). |
| `seed/` | Datos semilla: taxonomía, librerías, reglas, catálogos, adaptadores. |
| `tests/` | Pruebas de Python y archivos golden de exportación. |
| `docs/` | Manual de usuario, arquitectura, algoritmos, seguridad. |
| `dist/` | Salida de compilación (no versionada). |

## Convenciones

- **Idioma.** Todo lo visible en el libro (hojas, etiquetas, mensajes,
  formularios) va en español. Todo el código —identificadores, comentarios,
  commits y documentación técnica— va en inglés. Esto permite traducir el libro
  completando una columna del `Diccionario`, sin tocar lógica.
- **Sin valores mágicos.** Toda constante de negocio vive en la hoja `Parametros`
  o en un archivo de `seed/`, nunca incrustada en el código.
- **Un commit por unidad lógica de trabajo.**
