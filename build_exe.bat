@echo off
setlocal
cd /d "%~dp0"

set "VENV=.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [1/4] Creating virtual environment in "%VENV%" ...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: failed to create venv. Please install Python and add it to PATH.
        pause
        exit /b 1
    )
)

echo [2/4] Installing Pillow + PyInstaller ...
"%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt pyinstaller

echo [3/4] Building exe ...
"%PY%" -m PyInstaller --noconfirm --clean osu_skin_tool.spec

echo [4/4] Done. Output: dist\OsuSkinMaker.exe
pause
endlocal
