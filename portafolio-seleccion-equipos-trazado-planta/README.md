# Unir Portafolio — Selección de Equipos y Trazado de Planta

Script para unir en un solo PDF todos los archivos del portafolio estudiantil,
clasificándolos y ordenándolos automáticamente por sección (portada, notas de
clase, exámenes, asignaciones, laboratorios, diapositivas, problemas, otros).

## Uso

1. Instala la dependencia:

   ```bash
   pip install -r requirements.txt
   ```

2. Coloca todos los PDF del portafolio en esta carpeta.

3. Ejecuta el script:

   ```bash
   python unir_portafolio.py             # une los PDF
   python unir_portafolio.py --preview   # solo muestra el orden detectado
   ```

El resultado se guarda como `Portafolio_Seleccion_Equipos_Trazado_Planta.pdf`,
con marcadores navegables (uno por archivo original).

## Ajustar la clasificación

Las secciones y sus palabras clave se definen en la lista `SECCIONES` dentro
de `unir_portafolio.py`. Cada archivo se asigna a la primera sección cuyas
palabras clave aparezcan en su nombre (sin distinguir mayúsculas/minúsculas).
Los archivos que no coincidan con ninguna sección van al final, en "Otros".
