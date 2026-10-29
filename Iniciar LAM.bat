@echo off
setlocal
title Sistema LAM
cd /d "%~dp0"

rem Sistema LAM - arranque local. Doble clic para abrir la aplicacion en el navegador.
rem Los datos (pacientes, evaluaciones, fotos) quedan en la carpeta "datos" junto a este archivo.

if not exist "frontend\dist\index.html" (
  echo [Error] Falta la interfaz compilada: frontend\dist
  echo Genere el paquete con scripts\empaquetar.ps1 en el equipo de desarrollo,
  echo o ejecute "npm run build" dentro de la carpeta frontend.
  pause
  exit /b 1
)

where uv >nul 2>nul
if %errorlevel%==0 goto run
if exist "%USERPROFILE%\.local\bin\uv.exe" goto addpath
echo Instalando uv (solo la primera vez, requiere internet)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
:addpath
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

:run
echo.
echo Iniciando Sistema LAM...
echo La primera vez se descargan Python y las librerias: puede tardar unos minutos.
cd backend
uv run --frozen --no-dev python -m app.launcher
if errorlevel 1 (
  echo.
  echo La aplicacion se cerro con un error. Revise el mensaje de arriba.
)
pause
