@echo off
title Text Line Changer — Builder
echo.
echo ============================================
echo   Text Line Changer — EXE Builder
echo ============================================
echo.

:: Controleer of Python beschikbaar is
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python niet gevonden. Download het via https://www.python.org/downloads/
    echo        Zorg dat je "Add Python to PATH" aanvinkt tijdens de installatie.
    pause
    exit /b 1
)

echo [1/4] Cache en oude build opruimen...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
del /q TextLineChanger.spec 2>nul
del /q *.pyc 2>nul
echo       Klaar.

echo [2/4] Afhankelijkheden installeren...
pip install customtkinter==5.2.2 pyinstaller pillow --quiet
if errorlevel 1 (
    echo [FOUT] Installatie mislukt. Controleer je internetverbinding.
    pause
    exit /b 1
)

echo [3/4] EXE bouwen...
pyinstaller --onefile --windowed ^
    --name "TextLineChanger" ^
    --icon="app.ico" ^
    --collect-data customtkinter ^
    text_line_changer.py

if errorlevel 1 (
    echo [FOUT] Build mislukt. Zie de foutmelding hierboven.
    pause
    exit /b 1
)

echo [4/4] Opruimen...
rmdir /s /q build 2>nul
del /q TextLineChanger.spec 2>nul
rmdir /s /q __pycache__ 2>nul

echo.
echo ============================================
echo   Klaar! Je EXE staat in de map: dist\
echo   Bestand: dist\TextLineChanger.exe
echo ============================================
echo.
pause
