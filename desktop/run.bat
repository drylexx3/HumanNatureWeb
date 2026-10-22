@echo off
chcp 65001 >nul
title HumanNature x paste, write.
cd /d "%~dp0"

echo ==================================================
echo  HumanNature x paste, write. - Windows Edition
echo ==================================================
echo.

:: Detect Python launcher or executable
set PYTHON_BIN=
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_BIN=py -3
    goto :found_python
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_BIN=python
    goto :found_python
)

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_BIN=python3
    goto :found_python
)

echo [ERROR] No se encontro Python en tu sistema.
echo.
echo Para ejecutar la suite en Windows:
echo 1. Descarga Python 3 desde: https://www.python.org/downloads/
echo 2. IMPORTANTE: Marca la casilla "Add python.exe to PATH" durante la instalacion.
echo 3. Vuelve a ejecutar este archivo (run.bat).
echo.
pause
exit /b 1

:found_python
echo Python detectado. Instalando / comprobando dependencias...
%PYTHON_BIN% -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo.
echo Iniciando aplicacion...
%PYTHON_BIN% pastewrite.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] La aplicacion se cerro con codigo de error %ERRORLEVEL%.
    pause
)
