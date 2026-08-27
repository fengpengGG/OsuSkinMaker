@echo off
setlocal
cd /d "%~dp0"

set "VENV=.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PYW=%VENV%\Scripts\pythonw.exe"

if not exist "%PY%" (
    echo [1/3] Creating virtual environment in "%VENV%" ...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: failed to create venv. Please install Python and add it to PATH.
        pause
        exit /b 1
    )
)

echo [2/3] Installing dependencies (Pillow) ...
"%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo [3/3] Launching ...
start "" "%PYW%" main.py
endlocal
