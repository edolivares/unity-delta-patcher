# Navega al directorio donde está el script
Set-Location -Path $PSScriptRoot

Write-Host "Ejecutando script de generación de parches..."

# Ejecuta el script de Python
python ./generate_patches.py

Pause
