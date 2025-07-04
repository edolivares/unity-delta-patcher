#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar un manifest de archivos con hashes SHA256
Genera un archivo files_manifest.json con información de todos los archivos en la carpeta especificada
"""

import os
import json
import hashlib
import argparse
import sys
from pathlib import Path

def calculate_sha256(file_path):
    """Calcula el hash SHA256 de un archivo"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Leer el archivo en chunks para archivos grandes
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error al calcular hash de {file_path}: {e}")
        return None

def get_file_size(file_path):
    """Obtiene el tamaño de un archivo en bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        print(f"Error al obtener tamaño de {file_path}: {e}")
        return 0

def read_version(version_file):
    """Lee la versión del archivo version.txt"""
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
        return version
    except Exception as e:
        print(f"Error al leer versión de {version_file}: {e}")
        return "0.0.0"

def scan_directory(directory_path, base_path=""):
    """Escanea recursivamente un directorio y retorna información de todos los archivos"""
    files_info = []
    
    try:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Calcular la ruta relativa sin incluir el directorio base
                relative_path = os.path.relpath(file_path, directory_path)
                if base_path:
                    relative_path = os.path.join(base_path, relative_path)
                
                # Calcular hash y tamaño
                file_hash = calculate_sha256(file_path)
                file_size = get_file_size(file_path)
                
                if file_hash is not None:
                    files_info.append({
                        "path": relative_path,
                        "size": file_size,
                        "sha256": file_hash
                    })
                    print(f"Procesado: {relative_path} ({file_size} bytes)")
                else:
                    print(f"Error: No se pudo procesar {relative_path}")
    
    except Exception as e:
        print(f"Error al escanear directorio {directory_path}: {e}")
    
    return files_info

def generate_manifest_hash(manifest_data):
    """Genera un hash SHA256 del contenido del manifest (sin incluir manifest_hash)"""
    # Crear una copia del manifest sin la clave manifest_hash
    manifest_copy = manifest_data.copy()
    if 'manifest_hash' in manifest_copy:
        del manifest_copy['manifest_hash']
    
    # Convertir a JSON y calcular hash
    manifest_json = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(manifest_json.encode('utf-8')).hexdigest()

def validate_manifest_hash(manifest_data):
    """Valida que el manifest_hash del archivo es correcto"""
    # Obtener el hash almacenado en el manifest
    stored_hash = manifest_data.get('manifest_hash')
    if not stored_hash:
        return False, "No se encontró manifest_hash en el archivo"
    
    # Generar el hash del contenido actual (sin manifest_hash)
    calculated_hash = generate_manifest_hash(manifest_data)
    
    # Comparar hashes
    if stored_hash == calculated_hash:
        return True, f"✅ Hash válido: {stored_hash}"
    else:
        return False, f"❌ Hash inválido!\n  Almacenado: {stored_hash}\n  Calculado:  {calculated_hash}"

def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Genera un manifest de archivos con hashes SHA256",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python generate_manifest.py                    # Usa carpeta 'Old' por defecto
  python generate_manifest.py --source New       # Usa carpeta 'New'
  python generate_manifest.py -s New -o new_manifest.json  # Especifica carpeta y archivo de salida
  python generate_manifest.py --help            # Muestra esta ayuda
        """
    )
    
    parser.add_argument(
        '-s', '--source',
        default='Old',
        help='Carpeta de origen para generar el manifest (por defecto: Old)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Archivo de salida para el manifest (por defecto: files_manifest.json dentro de la carpeta de origen)'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='No validar el hash del manifest después de generarlo'
    )
    
    return parser.parse_args()

def main():
    """Función principal"""
    # Parsear argumentos
    args = parse_arguments()
    
    print("Iniciando generación del manifest de archivos...")
    print(f"Carpeta de origen: {args.source}")
    
    # Configurar rutas
    source_dir = args.source
    version_file = os.path.join(source_dir, "version.txt")
    
    # Si no se especifica archivo de salida, usar el por defecto dentro de la carpeta de origen
    if args.output is None:
        output_file = os.path.join(source_dir, "files_manifest.json")
    else:
        output_file = args.output
    
    print(f"Archivo de salida: {output_file}")
    
    # Verificar que existe la carpeta de origen
    if not os.path.exists(source_dir):
        print(f"Error: La carpeta {source_dir} no existe")
        sys.exit(1)
    
    # Leer versión
    version = read_version(version_file)
    print(f"Versión del juego: {version}")
    
    # Crear estructura del manifest
    manifest = {
        "version": version,
        "files": []
    }
    
    # Procesar archivos en la raíz de la carpeta de origen
    # NOTA: files_manifest.json se excluye para evitar dependencia circular en el hash
    print(f"\nProcesando archivos en la raíz de {source_dir}...")
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        if os.path.isfile(item_path) and item != "files_manifest.json":
            file_hash = calculate_sha256(item_path)
            file_size = get_file_size(item_path)
            
            if file_hash is not None:
                manifest["files"].append({
                    "path": item,
                    "size": file_size,
                    "sha256": file_hash
                })
                print(f"Procesado: {item} ({file_size} bytes)")
    
    # Procesar archivos en Edupie_Data
    edupie_data_dir = os.path.join(source_dir, "Edupie_Data")
    if os.path.exists(edupie_data_dir):
        print(f"\nProcesando archivos en Edupie_Data...")
        edupie_files = scan_directory(edupie_data_dir, "Edupie_Data")
        manifest["files"].extend(edupie_files)
    
    # Calcular tamaño total del build
    build_total_size = sum(file_info["size"] for file_info in manifest["files"])
    manifest["build_total_size"] = build_total_size
    
    # Guardar el manifest SIN el hash primero
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\nManifest guardado temporalmente: {output_file}")
        print(f"Total de archivos procesados: {len(manifest['files'])}")
        print(f"Tamaño total del build: {build_total_size:,} bytes ({build_total_size / (1024*1024*1024):.2f} GB)")
        
        # Generar hash del manifest DESPUÉS de guardar el archivo
        print("\nGenerando hash del manifest...")
        manifest_hash = generate_manifest_hash(manifest)
        
        # Agregar el hash al manifest
        manifest["manifest_hash"] = manifest_hash
        
        # Guardar el manifest FINAL con el hash
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"Hash del manifest: {manifest_hash}")
        
        # Validar el hash del manifest (a menos que se especifique --no-validate)
        if not args.no_validate:
            print("\nValidando hash del manifest...")
            is_valid, validation_message = validate_manifest_hash(manifest)
            print(validation_message)
            
            if is_valid:
                print("🎉 Proceso completado exitosamente - Manifest válido")
            else:
                print("⚠️  Advertencia: El manifest_hash no es válido")
        else:
            print("🎉 Proceso completado exitosamente")
        
    except Exception as e:
        print(f"Error al guardar el manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 