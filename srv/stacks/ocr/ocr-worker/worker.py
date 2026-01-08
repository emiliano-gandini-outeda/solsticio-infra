import os
import time
from pathlib import Path
import subprocess

UPLOAD_DIR = Path("/app/uploads")
RESULT_DIR = Path("/app/results")

# Crear carpetas si no existen
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

def process_file(file_path: Path):
    """Convierte el archivo en texto usando tesseract"""
    output_file = RESULT_DIR / (file_path.stem + ".txt")
    try:
        # Comando OCR
        subprocess.run([
            "tesseract",
            str(file_path),
            str(output_file.with_suffix('')),
            "--oem", "3",
            "--psm", "3"
        ], check=True)
        print(f"[OK] {file_path.name} -> {output_file.name}")
        # Borrar el archivo procesado
        file_path.unlink()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {file_path.name}: {e}")

def main_loop():
    print("Worker OCR iniciado…")
    while True:
        files = list(UPLOAD_DIR.glob("*"))
        if files:
            for f in files:
                process_file(f)
        else:
            time.sleep(2)  # Espera antes de buscar nuevos archivos

if __name__ == "__main__":
    main_loop()
