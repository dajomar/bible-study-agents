# ============================================================
# setup_scheduler.ps1
# Configura Windows Task Scheduler para Bible Study
# Ejecutar una sola vez como Administrador en el servidor Windows
# ============================================================

# ============================================================
# CONFIGURACIÓN — ajustar según el servidor
# ============================================================

$PROYECTO_PATH = "D:\proyectos\bible-study-agents"   # Ruta del proyecto en Windows
$PYTHON_EXE    = "C:\Users\david\AppData\Local\Programs\Python\Python311\python.exe"                              # O ruta absoluta: "C:\Python311\python.exe"
$HORA_EJECUCION = "05:00"
$NOMBRE_TAREA   = "BibleStudy-Analisis"

# ============================================================
# CREAR TAREA
# ============================================================

Write-Host "Configurando tarea: $NOMBRE_TAREA" -ForegroundColor Cyan

# Acción: correr el agente
$accion = New-ScheduledTaskAction `
    -Execute $PYTHON_EXE `
    -Argument "D:\proyectos\bible-study-agents\bible-study-agents\agents\agente_0_analisis.py" `
    -WorkingDirectory $PROYECTO_PATH

# Trigger: todos los días a las 05:00
$trigger = New-ScheduledTaskTrigger -Daily -At $HORA_EJECUCION

# Configuración: timeout 1 hora, reintentar si falla
$config = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Registrar la tarea (requiere permisos de Administrador)
Register-ScheduledTask `
    -TaskName   $NOMBRE_TAREA `
    -Action     $accion `
    -Trigger    $trigger `
    -Settings   $config `
    -RunLevel   Highest `
    -Force

Write-Host ""
Write-Host "Tarea registrada exitosamente:" -ForegroundColor Green
Write-Host "  Nombre:   $NOMBRE_TAREA"
Write-Host "  Horario:  todos los dias a las $HORA_EJECUCION"
Write-Host "  Proyecto: $PROYECTO_PATH"
Write-Host "  Python:   $PYTHON_EXE"
Write-Host ""
Write-Host "Para verificar:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName '$NOMBRE_TAREA'"
Write-Host ""
Write-Host "Para ejecutar manualmente:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$NOMBRE_TAREA'"
Write-Host ""
Write-Host "Para eliminar la tarea:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '$NOMBRE_TAREA' -Confirm:`$false"
