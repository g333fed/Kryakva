@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Kryakva v0.1.6 ===
py -V
py -m app.main
pause
