Attribute VB_Name = "modSmokeTest"
'==============================================================================
' modSmokeTest
'
' Phase 1 pipeline probe. Its only job is to prove that the build imported a
' VBA component into the workbook and that the component can be called back
' over COM. It carries no business logic and is removed once the real modules
' land, but its shape is the template every module follows: Option Explicit,
' a labelled error handler, and explicit cleanup.
'==============================================================================
Option Explicit

Private Const MODULE_NAME As String = "modSmokeTest"
Private Const PROBE_TOKEN As String = "RCM-PIPELINE-OK"

'------------------------------------------------------------------------------
' Returns a token the build asserts on, plus the host Excel version, so a
' successful call proves both the import and the automation round trip.
'------------------------------------------------------------------------------
Public Function SmokeTest_Ping() As String
    On Error GoTo ErrHandler

    SmokeTest_Ping = PROBE_TOKEN & "|" & Application.Version
    Exit Function

ErrHandler:
    SmokeTest_Ping = "ERROR|" & MODULE_NAME & "|" & Err.Number & "|" & Err.Description
End Function

'------------------------------------------------------------------------------
' Reports how many worksheets the workbook holding this module contains.
' Used by the build to confirm the VBA project is bound to the right workbook.
'------------------------------------------------------------------------------
Public Function SmokeTest_SheetCount() As Long
    On Error GoTo ErrHandler

    SmokeTest_SheetCount = ThisWorkbook.Worksheets.Count
    Exit Function

ErrHandler:
    SmokeTest_SheetCount = -1
End Function

'------------------------------------------------------------------------------
' Exercises the bulk-write guard rails: state is switched off before writing
' and restored on every exit path, including the error handler. Every module
' that writes in bulk repeats this pattern.
'------------------------------------------------------------------------------
Public Function SmokeTest_StateGuard() As Boolean
    Dim previousScreenUpdating As Boolean
    Dim previousEnableEvents As Boolean
    Dim previousCalculation As XlCalculation

    On Error GoTo ErrHandler

    previousScreenUpdating = Application.ScreenUpdating
    previousEnableEvents = Application.EnableEvents
    previousCalculation = Application.Calculation

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    ' A real module would write here.

    SmokeTest_StateGuard = True

CleanExit:
    Application.Calculation = previousCalculation
    Application.EnableEvents = previousEnableEvents
    Application.ScreenUpdating = previousScreenUpdating
    Exit Function

ErrHandler:
    SmokeTest_StateGuard = False
    Resume CleanExit
End Function
