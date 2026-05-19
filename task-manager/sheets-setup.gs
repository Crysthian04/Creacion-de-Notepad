/**
 * SETUP SCRIPT — Almacén de Repuestos · Task Manager
 *
 * CÓMO USAR:
 * 1. Abre tu Google Sheet.
 * 2. Ve a Extensiones > Apps Script.
 * 3. Pega este código completo.
 * 4. Corre setupSheet() una sola vez para crear la hoja "Tareas" con encabezados
 *    y pre-cargar las 16 semanas del plan como tareas de fondo.
 * 5. Corre generateGanttSheet() en cualquier momento para generar/actualizar
 *    la pestaña "Gantt" con colores y barras dentro de Sheets.
 *
 * Después de correr setupSheet(), usa la app web (index.html) con el ID de
 * esta hoja para gestionar tareas en tiempo real.
 */

const SHEET_NAME  = 'Tareas';
const GANTT_NAME  = 'Gantt';
const HEADERS     = ['ID','Nombre','Fase','Prioridad','FechaInicio','FechaVencimiento',
                     'FechaCompletado','Estado','Notas','QuickWin','EsPlan','SemanaPlan'];

const PHASE_COLORS = {
  'phase-1': { bg: '#e85d3a', fg: '#ffffff' },
  'phase-2': { bg: '#3a8fe8', fg: '#ffffff' },
  'phase-3': { bg: '#3ae87a', fg: '#0e1117' },
  'personal': { bg: '#f0c040', fg: '#0e1117' },
};

const PLAN_WEEKS = [
  { week:1,  phase:'phase-1', qw:true,  title:'Diagnóstico inicial y lista de emergencia' },
  { week:2,  phase:'phase-1', qw:false, title:'Limpieza Oracle — Registros inválidos y stocks negativos' },
  { week:3,  phase:'phase-1', qw:false, title:'Limpieza Oracle — Equipos asociados y proveedores' },
  { week:4,  phase:'phase-1', qw:true,  title:'Excel Maestro + Inventario Total #1' },
  { week:5,  phase:'phase-1', qw:false, title:'Estadísticas de uso — Sin movimiento y consumos anómalos' },
  { week:6,  phase:'phase-1', qw:true,  title:'Reporte ejecutivo Fase 1 — Cierre y aprobación' },
  { week:7,  phase:'phase-2', qw:false, title:'Análisis de máquinas y metodología de criticidad normativa' },
  { week:8,  phase:'phase-2', qw:false, title:'Clasificación CRÍTICO/IMPORTANTE/MENOR + Inventario Total #2' },
  { week:9,  phase:'phase-2', qw:false, title:'Cálculo estadístico de Mínimos, Máximos y Punto de Reorden' },
  { week:10, phase:'phase-2', qw:true,  title:'Power BI — Dashboard operativo con semáforo de stock' },
  { week:11, phase:'phase-2', qw:false, title:'Planes de Mantenimiento y costos por máquina' },
  { week:12, phase:'phase-2', qw:true,  title:'Reporte ejecutivo Fase 2 + Inventario Total #3' },
  { week:13, phase:'phase-3', qw:false, title:'Análisis ABC del inventario completo' },
  { week:14, phase:'phase-3', qw:false, title:'Dashboard Power BI completo y final' },
  { week:15, phase:'phase-3', qw:false, title:'Documentación, procedimientos y dataset consolidado' },
  { week:16, phase:'phase-3', qw:true,  title:'Presentación final · Cierre + Inventario Total #4' },
];

// ─── MAIN SETUP ───────────────────────────────────────────────────────────────
function setupSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  } else {
    const existing = sheet.getLastRow();
    if (existing > 0) {
      const ui = SpreadsheetApp.getUi();
      const resp = ui.alert(
        'La hoja "Tareas" ya existe',
        '¿Deseas limpiarla y volver a configurar? Esto borrará todos los datos existentes.',
        ui.ButtonSet.YES_NO
      );
      if (resp !== ui.Button.YES) { ui.alert('Setup cancelado.'); return; }
      sheet.clearContents();
      sheet.clearFormats();
    }
  }

  // Headers row
  const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
  headerRange.setValues([HEADERS]);
  headerRange.setBackground('#161b27');
  headerRange.setFontColor('#8a95aa');
  headerRange.setFontFamily('Barlow Condensed');
  headerRange.setFontWeight('bold');
  headerRange.setFontSize(10);
  headerRange.setBorder(false, false, true, false, false, false, '#252d3d', SpreadsheetApp.BorderStyle.SOLID);

  // Freeze header
  sheet.setFrozenRows(1);
  sheet.setFrozenColumns(2);

  // Column widths
  sheet.setColumnWidth(1, 120);  // ID
  sheet.setColumnWidth(2, 280);  // Nombre
  sheet.setColumnWidth(3, 100);  // Fase
  sheet.setColumnWidth(4, 80);   // Prioridad
  sheet.setColumnWidth(5, 110);  // FechaInicio
  sheet.setColumnWidth(6, 120);  // FechaVencimiento
  sheet.setColumnWidth(7, 120);  // FechaCompletado
  sheet.setColumnWidth(8, 100);  // Estado
  sheet.setColumnWidth(9, 200);  // Notas
  sheet.setColumnWidth(10, 80);  // QuickWin
  sheet.setColumnWidth(11, 70);  // EsPlan
  sheet.setColumnWidth(12, 90);  // SemanaPlan

  // Ask for project start date
  const ui = SpreadsheetApp.getUi();
  const resp = ui.prompt(
    'Fecha de inicio del proyecto',
    'Ingresa la fecha de inicio de la Semana 1 (formato YYYY-MM-DD):',
    ui.ButtonSet.OK_CANCEL
  );
  if (resp.getSelectedButton() !== ui.Button.OK) { ui.alert('No se ingresó fecha. Las semanas del plan no se cargarán con fechas reales.'); return; }

  const startDateStr = resp.getResponseText().trim();
  const startDate = new Date(startDateStr + 'T00:00:00');
  if (isNaN(startDate.getTime())) { ui.alert('Fecha inválida. Usa formato YYYY-MM-DD.'); return; }

  // Pre-load 16 plan weeks
  const rows = [];
  PLAN_WEEKS.forEach(pw => {
    const weekStart = new Date(startDate);
    weekStart.setDate(weekStart.getDate() + (pw.week - 1) * 7);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    rows.push([
      `PLAN-S${pw.week}`,
      pw.title,
      pw.phase,
      pw.qw ? 'critica' : 'alta',
      Utilities.formatDate(weekStart, 'UTC', 'yyyy-MM-dd'),
      Utilities.formatDate(weekEnd,   'UTC', 'yyyy-MM-dd'),
      '',
      'Pendiente',
      `Semana ${pw.week} del Plan de Trabajo · Almacén de Repuestos`,
      pw.qw ? 'si' : 'no',
      'si',
      String(pw.week),
    ]);
  });

  if (rows.length > 0) {
    const dataRange = sheet.getRange(2, 1, rows.length, HEADERS.length);
    dataRange.setValues(rows);
    formatDataRows(sheet, 2, rows.length);
  }

  // Apply conditional formatting for status column (H = col 8)
  applyConditionalFormats(sheet);

  // Store project start date in a named range for reference
  try {
    const namedRanges = ss.getNamedRanges();
    namedRanges.forEach(nr => { if (nr.getName() === 'ProjectStartDate') nr.remove(); });
    const cell = sheet.getRange('A1');
    ss.setNamedRange('ProjectStartDate', cell);
    PropertiesService.getScriptProperties().setProperty('projectStartDate', startDateStr);
  } catch(e) {}

  ui.alert('✅ Setup completado', `Hoja "Tareas" creada con las 16 semanas del plan.\nFecha de inicio: ${startDateStr}\n\nAhora puedes usar la app web con el ID de esta hoja.`, ui.ButtonSet.OK);
}

// ─── FORMAT DATA ROWS ─────────────────────────────────────────────────────────
function formatDataRows(sheet, startRow, count) {
  const range = sheet.getRange(startRow, 1, count, HEADERS.length);
  range.setBackground('#161b27');
  range.setFontColor('#e8ecf4');
  range.setFontFamily('Barlow');
  range.setFontSize(10);
  range.setVerticalAlignment('middle');
  sheet.setRowHeightsForced(startRow, count, 28);
}

// ─── CONDITIONAL FORMATS ──────────────────────────────────────────────────────
function applyConditionalFormats(sheet) {
  const maxRow = 500;
  const statusRange = sheet.getRange(2, 8, maxRow, 1); // Estado column

  const rules = [];
  const statusColors = {
    'Completado':  { bg: '#1a3a25', fg: '#3ae87a' },
    'En progreso': { bg: '#1a2d45', fg: '#3a8fe8' },
    'Pendiente':   { bg: '#2a1f0e', fg: '#f0c040' },
    'Bloqueado':   { bg: '#3a1515', fg: '#e83a3a' },
  };
  Object.entries(statusColors).forEach(([status, colors]) => {
    rules.push(
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo(status)
        .setBackground(colors.bg)
        .setFontColor(colors.fg)
        .setRanges([statusRange])
        .build()
    );
  });

  // Quick Win column (J = col 10)
  const qwRange = sheet.getRange(2, 10, maxRow, 1);
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('si')
      .setBackground('#2a2400')
      .setFontColor('#f0c040')
      .setRanges([qwRange])
      .build()
  );

  sheet.setConditionalFormatRules(rules);
}

// ─── GENERATE GANTT IN SHEETS ─────────────────────────────────────────────────
function generateGanttSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const tasksSheet = ss.getSheetByName(SHEET_NAME);
  if (!tasksSheet) { SpreadsheetApp.getUi().alert('Primero corre setupSheet().'); return; }

  let ganttSheet = ss.getSheetByName(GANTT_NAME);
  if (ganttSheet) {
    ganttSheet.clearContents();
    ganttSheet.clearFormats();
  } else {
    ganttSheet = ss.insertSheet(GANTT_NAME);
  }

  // Read tasks
  const lastRow = tasksSheet.getLastRow();
  if (lastRow < 2) { SpreadsheetApp.getUi().alert('No hay tareas en la hoja Tareas.'); return; }
  const data = tasksSheet.getRange(2, 1, lastRow - 1, HEADERS.length).getValues();

  const tasks = data.filter(r => r[0]).map(r => ({
    id:        r[0], name: r[1], phase: r[2],
    startDate: r[4] ? new Date(r[4]) : null,
    dueDate:   r[5] ? new Date(r[5]) : null,
    completed: r[6] ? new Date(r[6]) : null,
    status:    r[7], quickWin: r[9] === 'si', isPlan: r[10] === 'si',
  }));

  const projectStartStr = PropertiesService.getScriptProperties().getProperty('projectStartDate');
  const projectStart = projectStartStr ? new Date(projectStartStr + 'T00:00:00') : null;

  // Date range
  const allDates = tasks.flatMap(t => [t.startDate, t.dueDate, t.completed]).filter(Boolean);
  if (!allDates.length && !projectStart) { SpreadsheetApp.getUi().alert('No hay fechas definidas en las tareas.'); return; }

  let minDate = projectStart || allDates.reduce((a,b) => a < b ? a : b);
  let maxDate = allDates.reduce((a,b) => a > b ? a : b, minDate);
  if (projectStart) {
    const projEnd = new Date(projectStart); projEnd.setDate(projEnd.getDate() + 16*7);
    if (projEnd > maxDate) maxDate = projEnd;
  }
  // Add buffer
  minDate.setDate(minDate.getDate() - 3);
  maxDate.setDate(maxDate.getDate() + 7);

  const totalDays = Math.round((maxDate - minDate) / 86400000) + 1;
  const LABEL_COLS = 2;

  // Header row 1: Month labels
  ganttSheet.setRowHeight(1, 22);
  ganttSheet.getRange(1, 1).setValue('TAREA').setFontWeight('bold').setBackground('#161b27').setFontColor('#8a95aa').setFontFamily('Barlow Condensed');
  ganttSheet.getRange(1, 2).setValue('ESTADO').setFontWeight('bold').setBackground('#161b27').setFontColor('#8a95aa').setFontFamily('Barlow Condensed');

  let curDate = new Date(minDate);
  let col = LABEL_COLS + 1;
  while (curDate <= maxDate) {
    const ds = Utilities.formatDate(curDate, 'UTC', 'yyyy-MM-dd');
    ganttSheet.setColumnWidth(col, 18);
    const cell = ganttSheet.getRange(1, col);
    // Mark month start
    if (curDate.getDate() === 1) {
      const monthNames = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
      cell.setValue(monthNames[curDate.getMonth()]);
      cell.setBackground('#1e2535').setFontColor('#8a95aa').setFontSize(8).setFontFamily('Barlow Condensed').setFontWeight('bold');
    } else {
      cell.setBackground('#0e1117');
    }
    // Mark today
    const today = new Date(); today.setHours(0,0,0,0);
    if (curDate.getTime() === today.getTime()) {
      cell.setBackground('#2a2400').setFontColor('#f0c040').setValue('▼').setFontSize(8);
    }
    curDate.setDate(curDate.getDate() + 1);
    col++;
  }

  // Task rows
  tasks.forEach((t, i) => {
    const row = i + 2;
    ganttSheet.setRowHeight(row, 22);

    // Label
    const nameLabel = t.name.length > 35 ? t.name.slice(0, 34) + '…' : t.name;
    const nameCellBg = t.isPlan ? '#0e1117' : '#161b27';
    ganttSheet.getRange(row, 1).setValue(nameLabel)
      .setBackground(nameCellBg)
      .setFontColor(t.isPlan ? '#5a6478' : '#e8ecf4')
      .setFontSize(9).setFontFamily('Barlow');
    ganttSheet.getRange(row, 2).setValue(t.status)
      .setBackground(nameCellBg)
      .setFontSize(9).setFontFamily('Barlow Condensed');

    if (!t.startDate || !t.dueDate) return;

    const phColors = PHASE_COLORS[t.phase] || { bg: '#5a6478', fg: '#ffffff' };
    const barBg = t.status === 'Completado' ? '#2d3548' : phColors.bg;

    // Draw bar
    let d = new Date(minDate);
    let c = LABEL_COLS + 1;
    while (d <= maxDate) {
      const inBar = d >= t.startDate && d <= t.dueDate;
      if (inBar) {
        const cell = ganttSheet.getRange(row, c);
        const opacity = t.isPlan ? 0.3 : 1;
        if (t.isPlan) {
          cell.setBackground('#1e2535');
          cell.setBorder(false, false, false, false, false, false);
        } else {
          cell.setBackground(barBg);
        }
        // Mark due date
        if (Utilities.formatDate(d,'UTC','yyyy-MM-dd') === Utilities.formatDate(t.dueDate,'UTC','yyyy-MM-dd')) {
          cell.setBorder(false, false, false, true, false, false, phColors.bg, SpreadsheetApp.BorderStyle.MEDIUM);
        }
        // Mark Quick Win
        if (t.quickWin && Utilities.formatDate(d,'UTC','yyyy-MM-dd') === Utilities.formatDate(t.startDate,'UTC','yyyy-MM-dd')) {
          cell.setValue('⚡');
        }
      }
      d.setDate(d.getDate() + 1);
      c++;
    }

    // Mark completion if done
    if (t.status === 'Completado' && t.completed) {
      let cd = new Date(minDate); let cc = LABEL_COLS + 1;
      while (cd <= maxDate) {
        const inComp = cd >= t.startDate && cd <= t.completed;
        if (inComp) { ganttSheet.getRange(row, cc).setBackground(phColors.bg + '80'); }
        cd.setDate(cd.getDate() + 1); cc++;
      }
    }
  });

  // Label column widths
  ganttSheet.setColumnWidth(1, 240);
  ganttSheet.setColumnWidth(2, 90);
  ganttSheet.setFrozenColumns(2);
  ganttSheet.setFrozenRows(1);

  SpreadsheetApp.getUi().alert('✅ Gantt generado', `Pestaña "${GANTT_NAME}" creada con ${tasks.length} tareas.`, SpreadsheetApp.getUi().ButtonSet.OK);
}

// ─── MENU ─────────────────────────────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔧 Task Manager')
    .addItem('1. Configurar hoja (primera vez)', 'setupSheet')
    .addSeparator()
    .addItem('2. Generar/Actualizar Gantt en Sheets', 'generateGanttSheet')
    .addToUi();
}
