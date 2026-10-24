@echo off
chcp 65001 >nul
rem Nhap doi: nhap dup file nay de chay game (Windows)
cd /d "%~dp0"

if not exist ".venv-win\Scripts\python.exe" (
    echo Lan dau chay: dang tao moi truong va cai thu vien, vui long doi...
    python -m venv .venv-win
    if errorlevel 1 (
        echo Khong tim thay Python. Hay cai Python tai python.org va tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
    .venv-win\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Cai thu vien that bai. Kiem tra ket noi Internet roi chay lai.
        pause
        exit /b 1
    )
)

.venv-win\Scripts\python.exe main.py %*
if errorlevel 1 pause
