@echo off
setlocal
cd /d "%~dp0"
if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] First create backend venv and install requirements as in README.
  pause
  exit /b 1
)
if not exist "frontend\public\config.js" (
  copy /Y "frontend\public\config.example.js" "frontend\public\config.js" >nul
)
start "SECOM Backend" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --reload"
start "SECOM Frontend" /D "%~dp0frontend\public" cmd /k "py -3 -m http.server 8001"
echo Web: http://localhost:8001
echo API: http://127.0.0.1:8000/docs
echo Closing both new windows stops the local app without deleting data.
pause
