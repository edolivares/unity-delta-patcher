@echo off
cd /d "%~dp0"
echo Ejecutando script de generación de parches...
python generate_patches.py
pause
