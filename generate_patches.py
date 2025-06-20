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

    # Crear nombre de la carpeta del parche
    patch_folder_name = f"edupie-patch-v{old_version}-to-v{new_version}"
    patch_folder_path = os.path.join(PATCHES_DIR, patch_folder_name)
    patches_subfolder = os.path.join(patch_folder_path, 'patches')
    
    # Crear estructura de carpetas
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
    zip_path = os.path.join(PATCHES_DIR, zip_name)
    create_zip_archive(patch_folder_path, zip_path)
    
    print(f"✅ Archivo ZIP creado: {zip_path}")
    print(f"✅ Estructura de carpetas creada: {patch_folder_path}")

if __name__ == '__main__':
    main()
