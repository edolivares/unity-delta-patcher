import os
import hashlib
import json
import subprocess
import zipfile
import shutil

# Configuración de carpetas
OLD_DIR = 'Old'
NEW_DIR = 'New'
PATCHES_DIR = 'Patches'
XDELTA_EXECUTABLE = os.path.join('Utils', 'xdelta3.exe')

# Tipos de archivos y carpetas a ignorar
IGNORED_EXTENSIONS = ['.log', '.pdb', '.bak']
IGNORED_FOLDERS = ['Temp', 'Logs']

def should_ignore(file_path):
    return (
        any(ignored in file_path.split(os.sep) for ignored in IGNORED_FOLDERS) or
        any(file_path.endswith(ext) for ext in IGNORED_EXTENSIONS)
    )

def compute_sha256(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def relative_file_list(base_dir):
    file_list = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            rel_dir = os.path.relpath(root, base_dir)
            rel_file = os.path.join(rel_dir, file) if rel_dir != '.' else file
            if not should_ignore(rel_file):
                file_list.append(rel_file)
    return file_list

def ensure_patch_dir(path):
    full_path = os.path.join(PATCHES_DIR, os.path.dirname(path))
    os.makedirs(full_path, exist_ok=True)

def generate_patch(old_path, new_path, patch_path):
    subprocess.run([
        XDELTA_EXECUTABLE, '-e', '-s', old_path, new_path, patch_path
    ], check=True)

def read_version(version_file_path):
    if not os.path.exists(version_file_path):
        raise FileNotFoundError(f"No se encuentra el archivo de versión: {version_file_path}")
    
    with open(version_file_path, 'r') as vf:
        return vf.read().strip()

def create_zip_archive(patch_folder, zip_name):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(patch_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, patch_folder)
                zipf.write(file_path, arcname)

def calculate_zip_hash(zip_filename):
    """Calcula el hash SHA256 del archivo ZIP"""
    try:
        sha256_hash = hashlib.sha256()
        with open(zip_filename, "rb") as f:
            # Leer el archivo en chunks para archivos grandes
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        hash_value = sha256_hash.hexdigest()
        print(f"Hash SHA256 del ZIP: {hash_value}")
        return hash_value
    except Exception as e:
        print(f"Error al calcular hash del ZIP: {e}")
        return None

def get_zip_size(zip_filename):
    """Obtiene el tamaño del archivo ZIP en bytes"""
    try:
        size = os.path.getsize(zip_filename)
        print(f"Tamaño del ZIP: {size:,} bytes ({size / (1024*1024):.2f} MB)")
        return size
    except Exception as e:
        print(f"Error al obtener tamaño del ZIP: {e}")
        return 0

def calculate_uncompressed_size(patch_folder):
    """Calcula el tamaño total descomprimido de la carpeta del parche"""
    total_size = 0
    try:
        for root, dirs, files in os.walk(patch_folder):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size
    except Exception as e:
        print(f"Error al calcular tamaño descomprimido: {e}")
        return 0

def generate_patch_info(old_version, new_version, tag, filename, download_url, compressed_size, uncompressed_size, sha256):
    """Genera la estructura JSON de información del parche"""
    version_key = f"{old_version}_to_{new_version}"
    return {
        version_key: {
            "tag": tag,
            "filename": filename,
            "download_url": download_url,
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
            "sha256": sha256
        }
    }

def main():
    # Leer versiones
    old_version_file = os.path.join(OLD_DIR, 'version.txt')
    new_version_file = os.path.join(NEW_DIR, 'version.txt')
    
    try:
        old_version = read_version(old_version_file)
        new_version = read_version(new_version_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    print(f"Generando parche de v{old_version} a v{new_version}...")

    # Crear nombre de la carpeta del parche
    patch_folder_name = f"edupie-patch-v{old_version}-to-v{new_version}"
    version_folder_name = f"{old_version}_to_{new_version}"
    
    # Crear estructura de carpetas: Patches/0.0.0_to_0.0.1/edupie-patch-v0.0.0-to-v0.0.1/
    version_folder_path = os.path.join(PATCHES_DIR, version_folder_name)
    patch_folder_path = os.path.join(version_folder_path, patch_folder_name)
    patches_subfolder = os.path.join(patch_folder_path, 'patches')
    
    # Crear estructura de carpetas
    os.makedirs(version_folder_path, exist_ok=True)
    os.makedirs(patch_folder_path, exist_ok=True)
    os.makedirs(patches_subfolder, exist_ok=True)
    
    # Crear archivo version.txt en la carpeta del parche
    version_file_path = os.path.join(patch_folder_path, 'version.txt')
    with open(version_file_path, 'w') as vf:
        vf.write(f"v{old_version}-to-v{new_version}")
    
    manifest = {
        'version': new_version,
        'patch_files': []
    }

    new_files = relative_file_list(NEW_DIR)

    for rel_path in new_files:
        old_file = os.path.join(OLD_DIR, rel_path)
        new_file = os.path.join(NEW_DIR, rel_path)
        patch_file = os.path.join(patches_subfolder, rel_path + '.xdelta')

        # Crear directorio para el parche si es necesario
        patch_dir = os.path.dirname(patch_file)
        if patch_dir:
            os.makedirs(patch_dir, exist_ok=True)

        if not os.path.exists(old_file):
            print(f"[NUEVO] {rel_path}")
            generate_patch('NUL', new_file, patch_file)
        else:
            with open(old_file, 'rb') as f1, open(new_file, 'rb') as f2:
                if f1.read() == f2.read():
                    continue

            print(f"[MODIFICADO] {rel_path}")
            generate_patch(old_file, new_file, patch_file)

        manifest['patch_files'].append({
            'path': rel_path.replace("\\", "/"),
            'patch': (rel_path + '.xdelta').replace("\\", "/"),
            'size': os.path.getsize(new_file),
            'sha256': compute_sha256(new_file)
        })

    # Guardar manifest en la carpeta del parche
    manifest_path = os.path.join(patch_folder_path, 'patch_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2)
    
    print(f"\n✅ Manifest generado: {manifest_path}")
    
    # Crear archivo ZIP
    zip_name = f"{patch_folder_name}.zip"
    zip_path = os.path.join(version_folder_path, zip_name)
    create_zip_archive(patch_folder_path, zip_path)
    
    print(f"✅ Archivo ZIP creado: {zip_path}")
    print(f"✅ Estructura de carpetas creada: {patch_folder_path}")
    
    # Calcular tamaños y hash
    print("\nCalculando información del parche...")
    
    # Calcular tamaño descomprimido
    uncompressed_size = calculate_uncompressed_size(patch_folder_path)
    print(f"Tamaño descomprimido: {uncompressed_size:,} bytes ({uncompressed_size / (1024*1024):.2f} MB)")
    
    # Calcular tamaño comprimido
    compressed_size = get_zip_size(zip_path)
    
    # Calcular hash SHA256 del ZIP
    print("\nCalculando hash SHA256 del archivo ZIP...")
    sha256_hash = calculate_zip_hash(zip_path)
    if not sha256_hash:
        print("Error: No se pudo calcular el hash del ZIP")
        return
    
    # Generar información del parche
    tag = f"edupie-patch-v{old_version}-to-v{new_version}-pre"
    download_url = f"https://github.com/orion-system/edupie-releases/releases/download/{tag}/{zip_name}"
    
    patch_info = generate_patch_info(
        old_version=old_version,
        new_version=new_version,
        tag=tag,
        filename=zip_name,
        download_url=download_url,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
        sha256=sha256_hash
    )
    
    # Guardar archivo JSON con información del parche
    patch_info_filename = f"patch_info_{old_version}_to_{new_version}.json"
    patch_info_path = os.path.join(version_folder_path, patch_info_filename)
    
    try:
        with open(patch_info_path, 'w', encoding='utf-8') as f:
            json.dump(patch_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Información del parche generada exitosamente: {patch_info_path}")
        print(f"📦 Archivo ZIP: {zip_path}")
        print(f"📊 Tamaño comprimido: {compressed_size:,} bytes ({compressed_size / (1024*1024):.2f} MB)")
        print(f"📊 Tamaño descomprimido: {uncompressed_size:,} bytes ({uncompressed_size / (1024*1024):.2f} MB)")
        print(f"🔗 URL de descarga: {download_url}")
        print(f"🏷️  Tag: {tag}")
        print(f"📁 Ubicación: {version_folder_path}")
        
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {e}")

if __name__ == '__main__':
    main()
