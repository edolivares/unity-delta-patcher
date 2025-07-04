#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar información de release con archivo ZIP
Genera un archivo JSON con información de la versión, incluyendo archivo ZIP comprimido
"""

import os
import json
import hashlib
import zipfile
from pathlib import Path

def read_version(version_file):
    """Lee la versión del archivo version.txt"""
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
        return version
    except Exception as e:
        print(f"Error al leer versión de {version_file}: {e}")
        return "0.0.0"

def get_uncompressed_size(manifest_file):
    """Obtiene el tamaño descomprimido desde el files_manifest.json"""
    try:
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Obtener el build_total_size del manifest
        uncompressed_size = manifest.get('build_total_size', 0)
        return uncompressed_size
    except Exception as e:
        print(f"Error al leer manifest {manifest_file}: {e}")
        return 0

def create_zip_file(source_dir, zip_filename):
    """Crea un archivo ZIP con el contenido de la carpeta (sin incluir la carpeta en sí)"""
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Recorrer todos los archivos en el directorio
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Calcular la ruta relativa para el ZIP (sin incluir el directorio base)
                    relative_path = os.path.relpath(file_path, source_dir)
                    
                    # Agregar archivo al ZIP
                    zipf.write(file_path, relative_path)
                    print(f"Agregado al ZIP: {relative_path}")
        
        print(f"Archivo ZIP creado exitosamente: {zip_filename}")
        return True
    except Exception as e:
        print(f"Error al crear archivo ZIP: {e}")
        return False

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

def generate_release_info(version, tag, filename, download_url, compressed_size, uncompressed_size, sha256):
    """Genera la estructura JSON de información de release"""
    return {
        version: {
            "tag": tag,
            "filename": filename,
            "download_url": download_url,
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
            "sha256": sha256
        }
    }

def main():
    """Función principal"""
    print("Iniciando generación de información de release...")
    
    # Configurar rutas
    makebuild_dir = "MakeBuild"
    version_file = os.path.join(makebuild_dir, "version.txt")
    manifest_file = os.path.join(makebuild_dir, "files_manifest.json")
    
    # Leer versión primero para crear las rutas
    version = read_version(version_file)
    print(f"Versión del juego: {version}")
    
    # Crear carpeta de builds si no existe
    builds_dir = "Builds"
    version_dir = os.path.join(builds_dir, f"v{version}")
    
    # Crear directorios si no existen
    os.makedirs(builds_dir, exist_ok=True)
    os.makedirs(version_dir, exist_ok=True)
    
    print(f"Carpeta de versión creada: {version_dir}")
    
    # Configurar archivos de salida en la carpeta de versión
    zip_filename = f"edupie-base-v{version}.zip"
    zip_path = os.path.join(version_dir, zip_filename)
    output_file = os.path.join(version_dir, f"release_info_v{version}.json")
    
    # Verificar que existe la carpeta MakeBuild
    if not os.path.exists(makebuild_dir):
        print(f"Error: La carpeta {makebuild_dir} no existe")
        return
    
    # Obtener tamaño descomprimido
    uncompressed_size = get_uncompressed_size(manifest_file)
    print(f"Tamaño descomprimido: {uncompressed_size:,} bytes ({uncompressed_size / (1024*1024*1024):.2f} GB)")
    
    print(f"Nombre del archivo ZIP: {zip_filename}")
    
    # Crear archivo ZIP
    print(f"\nCreando archivo ZIP desde {makebuild_dir}...")
    if not create_zip_file(makebuild_dir, zip_path):
        print("Error: No se pudo crear el archivo ZIP")
        return
    
    # Calcular tamaño comprimido
    compressed_size = get_zip_size(zip_path)
    
    # Calcular hash SHA256 del ZIP
    print("\nCalculando hash SHA256 del archivo ZIP...")
    sha256_hash = calculate_zip_hash(zip_path)
    if not sha256_hash:
        print("Error: No se pudo calcular el hash del ZIP")
        return
    
    # Generar información de release
    tag = f"v{version}-base"
    download_url = f"https://github.com/orion-system/edupie-releases/releases/download/{tag}/{zip_filename}"
    
    release_info = generate_release_info(
        version=version,
        tag=tag,
        filename=zip_filename,
        download_url=download_url,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
        sha256=sha256_hash
    )
    
    # Guardar archivo JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(release_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Información de release generada exitosamente: {output_file}")
        print(f"📦 Archivo ZIP: {zip_path}")
        print(f"📊 Tamaño comprimido: {compressed_size:,} bytes ({compressed_size / (1024*1024):.2f} MB)")
        print(f"📊 Tamaño descomprimido: {uncompressed_size:,} bytes ({uncompressed_size / (1024*1024*1024):.2f} GB)")
        print(f"🔗 URL de descarga: {download_url}")
        print(f"🏷️  Tag: {tag}")
        print(f"📁 Ubicación: {version_dir}")
        
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {e}")

if __name__ == "__main__":
    main() 