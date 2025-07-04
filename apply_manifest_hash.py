#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar hash SHA256 a un archivo JSON y agregarlo como campo hash_manifest
Permite especificar el archivo de origen y valida el hash después del proceso
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

def generate_manifest_hash(manifest_data):
    """Genera un hash SHA256 del contenido del manifest (sin incluir hash_manifest)"""
    # Crear una copia del manifest sin la clave hash_manifest
    manifest_copy = manifest_data.copy()
    if 'hash_manifest' in manifest_copy:
        del manifest_copy['hash_manifest']

    # Serializar JSON en formato compacto (sin espacios, sin saltos de línea)
    # Esto es equivalente a Formatting.None en C# con Newtonsoft.Json
    manifest_json = json.dumps(manifest_copy, separators=(',', ':'), ensure_ascii=False)
    
    print(f"JSON serializado para hash (compacto):")
    print(manifest_json)
    
    # Calcular hash SHA-256
    return hashlib.sha256(manifest_json.encode('utf-8')).hexdigest()

def validate_manifest_hash(manifest_data):
    """Valida que el hash_manifest del archivo es correcto"""
    # Obtener el hash almacenado en el manifest
    stored_hash = manifest_data.get('hash_manifest')
    if not stored_hash:
        return False, "No se encontró hash_manifest en el archivo"
    
    # Generar el hash del contenido actual (sin hash_manifest)
    calculated_hash = generate_manifest_hash(manifest_data)
    
    # Comparar hashes
    if stored_hash == calculated_hash:
        return True, f"✅ Hash válido: {stored_hash}"
    else:
        return False, f"❌ Hash inválido!\n  Almacenado: {stored_hash}\n  Calculado:  {calculated_hash}"

def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Aplica hash SHA256 a un archivo JSON y lo agrega como campo hash_manifest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python apply_manifest_hash.py --source manifest/edupie_path_chain_manifest.json
  python apply_manifest_hash.py -s manifest/edupie_path_chain_manifest.json
  python apply_manifest_hash.py --help
        """
    )
    
    parser.add_argument(
        '-s', '--source',
        required=True,
        help='Archivo JSON de origen al que se le aplicará el hash'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='No validar el hash del manifest después de aplicarlo'
    )
    
    return parser.parse_args()

def main():
    """Función principal"""
    # Parsear argumentos
    args = parse_arguments()
    
    print("Iniciando aplicación de hash al manifest...")
    print(f"Archivo de origen: {args.source}")
    
    # Verificar que existe el archivo de origen
    if not os.path.exists(args.source):
        print(f"Error: El archivo {args.source} no existe")
        sys.exit(1)
    
    # Leer el archivo JSON
    try:
        with open(args.source, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        print(f"✅ Archivo JSON leído exitosamente")
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
        sys.exit(1)
    
    # Calcular hash del contenido actual (sin hash_manifest)
    print("\nCalculando hash del contenido del manifest...")
    manifest_hash = generate_manifest_hash(manifest_data)
    
    if not manifest_hash:
        print("Error: No se pudo calcular el hash del manifest")
        sys.exit(1)
    
    print(f"Hash calculado: {manifest_hash}")
    
    # Agregar el hash al manifest
    manifest_data['hash_manifest'] = manifest_hash
    
    # Guardar el archivo actualizado
    try:
        with open(args.source, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Hash aplicado exitosamente al archivo: {args.source}")
        print(f"Hash agregado: {manifest_hash}")
        
        # Validar el hash del manifest (a menos que se especifique --no-validate)
        if not args.no_validate:
            print("\nValidando hash del manifest...")
            is_valid, validation_message = validate_manifest_hash(manifest_data)
            print(validation_message)
            
            if is_valid:
                print("🎉 Proceso completado exitosamente - Hash válido")
            else:
                print("⚠️  Advertencia: El hash_manifest no es válido")
        else:
            print("🎉 Proceso completado exitosamente")
        
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()