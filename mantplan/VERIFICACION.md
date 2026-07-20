# VERIFICACION.md — MantPlan v2.0.0

Reporte de verificación del entregable A tras el cambio estructural
(REGLA-2 con año ISO, `horas_ajustadas`/`horas_efectivas`, hojas
dimensionadas por datos, pegado en un bloque, tablas a 1.200 filas).
Fecha de la corrida: **2026-07-20** (ancla de los datos sintéticos).

## 1. Recálculo con motor de cálculo real

La variante `MantPlan_compatible.xlsx` (mismas plantillas de fórmula que el
principal, con `INDEX/MATCH` + rangos A1 en lugar de `XLOOKUP` + referencias
estructuradas) se recalculó por completo con LibreOffice Calc 24.2:

| Métrica | Valor |
|---|---:|
| Fórmulas recalculadas | **51.623** |
| Errores de fórmula (`#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`, `#N/A`, …) | **0** |

## 2. Comparación motor Python ↔ Excel recalculado

Cada valor del libro recalculado se comparó contra el motor Python
(`generar_mantplan.py`, funciones `regla_1` … `regla_10`), tolerancia 1e-6:

| Métrica | Valor |
|---|---:|
| Comparaciones automáticas | **7.587** |
| Desviaciones | **0** |

Cobertura de la comparación:

- Las 22 columnas calculadas de las 200 órdenes reales (incluye `semana` con
  año ISO, `horas_efectivas`, HHA, HHD y costos REGLA-8).
- Muestreo de filas provisionadas vacías (250, 700, 1.203): todas las
  calculadas en blanco y `en_plan = FALSO` — el blindaje de las 1.200 filas
  funciona.
- `id_operacion` de las 163 filas de EJECUCION (ahora última columna) + fila
  vacía.
- Las 336 filas de REGLA-5 (ASIGNACIONES).
- PERFIL_HH completo: la serie de semanas derivada por fórmula (60 posiciones
  contra la serie esperada 2026-S08 … 2027-S01) y las 7 métricas de REGLA-6
  para las ~25 semanas con datos × 5 especialidades; bloque REGLA-9 completo.
- ADHERENCIA: bloque semanal dinámico (60 filas) + desgloses por área,
  especialidad, coordinador, clasificación y técnico.
- BACKLOG por tramos, COSTOS por mes (plan y real), EQUIPOS_CRITICOS,
  zona de datos del gráfico de carga y los 11 chequeos de VALIDACION.

## 3. Casos de prueba pedidos

### 3.1 Cruce de fin de año — `2026-S53` y `2027-S01` son semanas distintas

| orden | fecha_inicio | semana (libro y Python) | anio (`YEAR`) |
|---|---|---|---|
| OT-000182 | 2026-12-29 | **2026-S53** | 2026 |
| OT-000183 | 2027-01-01 | **2026-S53** | **2027** |
| OT-000184 | 2027-01-05 | **2027-S01** | 2027 |

OT-000183 es la prueba del año ISO: `YEAR` da 2027 pero la semana pertenece a
2026-S53. Ambas semanas aparecen como filas separadas (visibles) al final de
la serie de PERFIL_HH y ADHERENCIA. El pliegue S53→S1 quedó eliminado.

### 3.2 Ajuste manual — `horas_estimadas` 8, `horas_ajustadas` 12 → todo usa 12

Orden **OT-000017** (MEC, preventiva, Técnico 01, martes de 2026-S30):

| Punto verificado | Con 8 h (sin ajuste) | Verificado con 12 h |
|---|---:|---:|
| `horas_efectivas` | 8 | **12** |
| PERFIL_HH · MEC 2026-S30 · hh_preventiva | 80 | **84** |
| PERFIL_HH · MEC 2026-S30 · % carga | 86,2 % | **89,5 %** |
| Gráfico de carga · barra Técnico 01 (2026-S30) | 31 | **35** = 30,45 verde + 4,55 rojo |
| HHA del martes / HHD | 8 / −1,91 | **12 / −5,91** |

Segundo ajuste (OT-000061, ELE, 6 → 4) para probar el sentido inverso:
ELE 2026-S30 prev 63, carga 97,3 %. VALIDACION reporta **2 órdenes
ajustadas** y **desviación total +2 h** (+4 − 2).

### 3.3 Recálculo de la variante compatible

**0 errores en 51.623 fórmulas** (tabla del §1), con los mismos números que
el motor Python en las 7.587 comparaciones del §2.

## 4. Qué NO se verificó (y por qué)

- **El archivo principal (`MantPlan.xlsx`) no se puede recalcular
  localmente**: LibreOffice 24.2 no evalúa `XLOOKUP` ni referencias
  estructuradas. Su corrección se infiere de que ambos modos salen de las
  mismas plantillas (`class Refs`) — la única diferencia es la función de
  búsqueda — más una auditoría sintáctica (XLOOKUP canónico `_xlfn.`, cero
  OFFSET/INDIRECT/columnas completas, cero enlaces externos, cero VBA).
  Falta el humo final en Excel real, que no existe en este entorno.
- **Renderizado visual**: gráficos (se auditó el XML: combo barras
  apiladas + línea con marcador en ejes compartidos), formato condicional,
  colores y anchos se verificaron por inspección del XML/objetos, no por
  captura de pantalla.
- **La hoja EXPORTAR** solo se verificó por ausencia de errores de fórmula
  (el texto armado no se comparó contra un esperado). Está pendiente su
  revisión funcional en el siguiente paso acordado.
- **Flujo de re-importación real** (pegar 800 filas nuevas y ver que todo
  recalcula) no se simuló; el blindaje de filas vacías y la provisión de
  fórmulas sí están verificados.
- El **comportamiento del ocultamiento de filas tras re-importar** (semanas
  nuevas nacen en filas ocultas) está documentado pero no es automatizable
  sin macros.

## 5. Supuestos tomados donde la instrucción era ambigua

1. **`horas_efectivas`**: la fórmula pedida era
   `IF(horas_ajustadas<>"", horas_ajustadas, horas_estimadas)`; se añadió un
   guardado interno para que una orden sin horas y sin ajuste quede vacía en
   lugar de 0.
2. **"Filas sin datos ocultas"**: el ocultamiento se aplica al generar el
   archivo (sin macros no puede ser reactivo). Documentado en README §4.
3. **Ventana de 4 semanas en desplegables**: se mantuvo la lista
   "(todos)" + 4 semanas del plan; el resto de semanas se analiza en las
   hojas de reporte, no en los selectores.
4. **`costo_plan` no se recalcula con el ajuste manual**: es el estándar del
   ERP. Si el ajuste de horas debiera repreciar el plan, hay que definirlo
   (tarifa por clasificación está en los datos de ejemplo, no en el motor).
5. **Área de impresión de PLAN_SEMANAL estática** (dinámica exigiría OFFSET,
   prohibido).
6. **Nombre de la hoja**: se mantiene `PLAN_SEMANAL` (nombre del PROYECTO.md);
   el pedido la llamó una vez `PROGRAMA_SEMANAL` — pendiente de confirmación.

## 6. Inconsistencias señaladas (pedido vs. modelo)

- **`horas_ajustadas` anclada a la fila**: sobrevive a la re-importación
  porque la columna M queda fuera del bloque pegado A:L, pero si el export
  siguiente trae las filas en otro orden, el ajuste queda sobre otra orden.
  Robustecerlo exige ajustes por `id_operacion` (propuesto para B).
- **`anio` (= `YEAR`) convive con el año ISO de `semana`**: en los días de
  cruce difieren (OT-000183: anio 2027, semana 2026-S53). Correcto para
  costos mensuales vs. planificación semanal, pero conviene no cruzar ambos
  campos en un mismo reporte.
- **Capacidad de 60 semanas**: los datos de ejemplo ya ocupan ~48 (backlog de
  150 días + órdenes de enero siguiente). Un histórico mayor a 60 semanas
  truncaría la serie; si el caso real lo necesita, subir `CAP_SEM`.
