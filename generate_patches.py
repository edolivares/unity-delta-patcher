import os
import hashlib
import json
import subprocess

# Configuración de carpetas
OLD_DIR = 'Old'
NEW_DIR = 'New'
PATCHES_DIR = 'Patches'
MANIFEST_PATH = 'patch_manifest.json'
VERSION_FILE = os.path.join(NEW_DIR, 'version.txt')
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

def main():
    if not os.path.exists(VERSION_FILE):
        print(f"ERROR: No se encuentra {VERSION_FILE}")
        return

    with open(VERSION_FILE, 'r') as vf:
        version = vf.read().strip()

    os.makedirs(PATCHES_DIR, exist_ok=True)
    manifest = {
        'version': version,
        'patch_files': []
    }

    new_files = relative_file_list(NEW_DIR)

    for rel_path in new_files:
        old_file = os.path.join(OLD_DIR, rel_path)
        new_file = os.path.join(NEW_DIR, rel_path)
        patch_file = os.path.join(PATCHES_DIR, rel_path + '.xdelta')

        if not os.path.exists(old_file):
            print(f"[NUEVO] {rel_path}")
            ensure_patch_dir(rel_path)
            generate_patch('NUL', new_file, patch_file)
        else:
            with open(old_file, 'rb') as f1, open(new_file, 'rb') as f2:
                if f1.read() == f2.read():
                    continue

            print(f"[MODIFICADO] {rel_path}")
            ensure_patch_dir(rel_path)
            generate_patch(old_file, new_file, patch_file)

        manifest['patch_files'].append({
            'path': rel_path.replace("\\", "/"),
            'patch': os.path.join(PATCHES_DIR, rel_path + '.xdelta').replace("\\", "/"),
            'size': os.path.getsize(new_file),
            'sha256': compute_sha256(new_file)
        })

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2)
    print(f"\n✅ Manifest generado: {MANIFEST_PATH}")

if __name__ == '__main__':
    main()
