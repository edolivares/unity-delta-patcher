# 🎮 BuildJuego - Sistema de Generación de Parches

Este proyecto automatiza la generación de parches delta para actualizaciones de juegos, utilizando archivos de manifiesto con hashes SHA256 y la herramienta xdelta3 para crear parches binarios eficientes.

## 📁 Estructura del Proyecto

### Carpetas Principales

- **`Old/`** - Contiene la versión anterior del juego (base para comparación)
- **`New/`** - Contiene la nueva versión del juego (versión a distribuir)
- **`MakeBuild/`** - Carpeta de trabajo donde se prepara la versión final para distribución
- **`Builds/`** - Almacena las versiones compiladas listas para distribución
- **`Patches/`** - Contiene todos los parches delta generados
- **`manifest/`** - Almacena archivos de manifiesto con información de versiones
- **`Utils/`** - Herramientas auxiliares (xdelta3.exe para generar parches binarios)

### Scripts Principales

- **`generate_manifest.py`** - Genera manifiestos de archivos con hashes SHA256
- **`generate_patches.py`** - Crea parches delta entre versiones
- **`build_release_info.py`** - Genera información de release con archivos ZIP
- **`apply_manifest_hash.py`** - Aplica y valida hashes de manifiestos
- **`run_patch_generator.bat`** - Script batch para ejecutar el generador de parches
- **`run_patch_generator.ps1`** - Script PowerShell para ejecutar el generador de parches

## 🚀 Cómo Usar el Sistema

### 1. Preparación de Versiones

1. **Coloca la versión anterior** en la carpeta `Old/`
2. **Coloca la nueva versión** en la carpeta `New/`
3. **Asegúrate de que cada versión tenga un archivo `version.txt`** con el número de versión

### 2. Generación de Manifiestos

```bash
# Generar manifiesto para la versión anterior
python generate_manifest.py --source Old

# Generar manifiesto para la nueva versión
python generate_manifest.py --source New
```

**¿Qué hace?**

- Escanea recursivamente todos los archivos en la carpeta especificada
- Calcula hashes SHA256 de cada archivo
- Genera un archivo `files_manifest.json` con información detallada
- Incluye tamaño total del build y versión del juego

### 3. Generación de Parches Delta

```bash
# Ejecutar desde línea de comandos
python generate_patches.py

# O usar los scripts de conveniencia
run_patch_generator.bat    # Windows Batch
run_patch_generator.ps1    # PowerShell
```

**¿Qué hace?**

- Compara archivos entre `Old/` y `New/`
- Genera parches `.xdelta` para archivos modificados
- Crea archivos nuevos para archivos que no existían
- Genera un manifiesto de parche con información de cada archivo
- Crea un archivo ZIP con todos los parches
- Estructura: `Patches/{version_old}_to_{version_new}/edupie-patch-v{old}-to-v{new}.zip`

### 4. Preparación de Build para Distribución

```bash
# Copiar nueva versión a MakeBuild
# (Esto se hace manualmente o con un script de copia)

# Generar información de release
python build_release_info.py
```

**¿Qué hace?**

- Toma el contenido de `MakeBuild/`
- Crea un archivo ZIP comprimido
- Calcula hash SHA256 del ZIP
- Genera información de release en formato JSON
- Guarda todo en `Builds/v{version}/`

### 5. Validación de Manifiestos

```bash
# Aplicar hash a un manifiesto
python apply_manifest_hash.py --source manifest/edupie_path_chain_manifest.json

# Validar hash de un manifiesto existente
python generate_manifest.py --source Old
```

**¿Qué hace?**

- Aplica un hash SHA256 al contenido del manifiesto
- Valida que el hash sea correcto
- Ayuda a detectar corrupción o modificaciones no autorizadas

## 📋 Flujo de Trabajo Completo

### Para una Nueva Actualización:

1. **Preparar versiones:**

   ```bash
   # Copiar versión anterior a Old/
   # Copiar nueva versión a New/
   # Asegurar que version.txt esté actualizado en ambas carpetas
   ```

2. **Generar manifiestos:**

   ```bash
   python generate_manifest.py --source Old
   python generate_manifest.py --source New
   ```

3. **Crear parches:**

   ```bash
   python generate_patches.py
   ```

4. **Preparar build final:**

   ```bash
   # Copiar contenido de New/ a MakeBuild/
   python build_release_info.py
   ```

5. **Validar integridad:**
   ```bash
   python apply_manifest_hash.py --source MakeBuild/files_manifest.json
   ```

## 🔧 Configuración

### Archivos de Configuración

- **`version.txt`** - Contiene el número de versión (ej: "1.2.3")
- **`files_manifest.json`** - Manifiesto con información de todos los archivos
- **`patch_manifest.json`** - Información de archivos incluidos en el parche

### Extensiones y Carpetas Ignoradas

El sistema ignora automáticamente:

- **Extensiones:** `.log`, `.pdb`, `.bak`
- **Carpetas:** `Temp`, `Logs`

## 📊 Estructura de Salida

### Parches Generados

```
Patches/
├── 1.0.0_to_1.0.1/
│   ├── edupie-patch-v1.0.0-to-v1.0.1.zip
│   └── edupie-patch-v1.0.0-to-v1.0.1/
│       ├── version.txt
│       ├── patch_manifest.json
│       └── patches/
│           ├── archivo1.xdelta
│           └── archivo2.xdelta
```

### Builds Finales

```
Builds/
├── v1.0.0/
│   ├── edupie-base-v1.0.0.zip
│   └── release_info_v1.0.0.json
└── v1.0.1/
    ├── edupie-base-v1.0.1.zip
    └── release_info_v1.0.1.json
```

## 🛠️ Requisitos

- **Python 3.6+**
- **xdelta3.exe** (incluido en `Utils/`)
- **Archivos de versión** con formato correcto

## 🔍 Verificación de Integridad

Todos los archivos incluyen hashes SHA256 para verificar integridad:

- **Archivos individuales** - Hash de cada archivo del juego
- **Manifiestos** - Hash del contenido JSON
- **Archivos ZIP** - Hash del archivo comprimido completo

## 📝 Notas Importantes

1. **Siempre verifica las versiones** antes de generar parches
2. **Mantén copias de seguridad** de las versiones anteriores
3. **Valida los hashes** después de cualquier modificación
4. **Los parches son incrementales** - cada parche va de una versión específica a otra
5. **El sistema es idempotente** - puedes ejecutar los scripts múltiples veces de forma segura

## 🆘 Solución de Problemas

### Error: "No se encuentra xdelta3.exe"

- Verifica que `Utils/xdelta3.exe` existe
- Descarga xdelta3 desde el repositorio oficial si es necesario

### Error: "No se encuentra version.txt"

- Asegúrate de que cada carpeta de versión tenga un archivo `version.txt`
- El formato debe ser simple: solo el número de versión (ej: "1.2.3")

### Error: "Hash inválido"

- El archivo puede estar corrupto
- Regenera el manifiesto desde la fuente original
- Verifica que no se haya modificado manualmente

---

**Desarrollado para automatizar el proceso de distribución de actualizaciones de juegos de manera segura y eficiente.**
