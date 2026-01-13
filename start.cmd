@echo off
setlocal

echo Starting backend...
start "backend" cmd /k "cd /d %~dp0 && python -m app.server"

echo Starting frontend...
start "frontend" cmd /k "cd /d %~dp0 && frontend_start.cmd"

endlocal
