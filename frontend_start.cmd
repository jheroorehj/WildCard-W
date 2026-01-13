@echo off
setlocal

cd /d %~dp0frontend

if not exist node_modules (
  echo Installing frontend dependencies...
  npm install
  if errorlevel 1 (
    echo npm install failed.
    exit /b 1
  )
)

echo Starting frontend dev server...
npm run dev

endlocal
