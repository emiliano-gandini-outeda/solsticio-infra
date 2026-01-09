import time
from pathlib import Path
import subprocess
import os
import sys
import redis
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Configuración
UPLOAD_DIR = Path("/app/uploads")
RESULT_DIR = Path("/app/results")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Crear directorios
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# Conectar a Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

logging.info("Worker OCR iniciado con Redis")
logging.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
logging.info(f"Upload dir: {UPLOAD_DIR}")
logging.info(f"Result dir: {RESULT_DIR}")

def update_job_status(job_id: str, status: str, message: str = ""):
    """Actualizar estado del trabajo en Redis"""
    try:
        redis_client.hset(f"job:{job_id}", "status", status)
        if message:
            redis_client.hset(f"job:{job_id}", "message", message)
    except Exception as e:
        logging.error(f"Error actualizando estado de {job_id}: {e}")

def pdf_to_images(pdf_path: Path, temp_dir: Path):
    """Convierte PDF a imágenes usando pdftoppm"""
    try:
        logging.info(f"Convirtiendo PDF a imágenes: {pdf_path.name}")
        
        # Usar pdftoppm para convertir PDF a imágenes PNG
        result = subprocess.run([
            "pdftoppm",
            "-png",
            "-r", "300",  # Resolución
            str(pdf_path),
            str(temp_dir / "page")
        ], check=True, capture_output=True, text=True)
        
        # Encontrar las imágenes generadas
        images = sorted(temp_dir.glob("*.png"))
        if images:
            logging.info(f"PDF convertido a {len(images)} imágenes")
            return images
        else:
            logging.error("No se generaron imágenes del PDF")
            return []
            
    except subprocess.CalledProcessError as e:
        logging.error(f"pdftoppm falló: {e.stderr}")
        return []

def process_image_with_tesseract(image_path: Path, output_base: Path):
    """Procesa una imagen con Tesseract"""
    try:
        result = subprocess.run([
            "tesseract",
            str(image_path),
            str(output_base),
            "-l", "spa+eng",
            "--oem", "3",
            "--psm", "3"
        ], check=True, capture_output=True, text=True)
        
        return result.returncode == 0
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Tesseract falló: {e.stderr}")
        return False

def process_pdf_with_ocr(file_path: Path, job_id: str):
    """Procesa un PDF con OCR"""
    temp_dir = RESULT_DIR / "temp" / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convertir PDF a imágenes
        images = pdf_to_images(file_path, temp_dir)
        if not images:
            return False
        
        # Procesar cada imagen
        all_text = []
        for i, img in enumerate(images, 1):
            logging.info(f"Procesando página {i}/{len(images)}")
            temp_output = temp_dir / f"page_{i}"
            
            if process_image_with_tesseract(img, temp_output):
                # Leer texto extraído
                text_file = Path(f"{temp_output}.txt")
                if text_file.exists():
                    with open(text_file, 'r', encoding='utf-8') as f:
                        page_text = f.read().strip()
                        if page_text:
                            all_text.append(page_text)
                
                # Limpiar archivos temporales
                text_file.unlink(missing_ok=True)
            img.unlink(missing_ok=True)  # Limpiar imagen
        
        # Guardar resultado
        if all_text:
            output_file = RESULT_DIR / f"{job_id}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n\n--- Página siguiente ---\n\n".join(all_text))
            logging.info(f"Resultado guardado: {output_file.name}")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error procesando PDF: {e}")
        return False
    finally:
        # Limpiar directorio temporal
        for f in temp_dir.glob("*"):
            f.unlink(missing_ok=True)
        temp_dir.rmdir()

def process_job(job_id: str):
    """Procesa un trabajo de la cola"""
    try:
        logging.info(f"Iniciando procesamiento de trabajo: {job_id}")
        update_job_status(job_id, "processing")
        
        # Obtener información del trabajo
        job_info = redis_client.hgetall(f"job:{job_id}")
        if not job_info:
            logging.error(f"Job no encontrado en Redis: {job_id}")
            return False
        
        file_path = Path(job_info.get("filepath", ""))
        if not file_path.exists():
            logging.error(f"Archivo no encontrado: {file_path}")
            update_job_status(job_id, "failed", "Archivo no encontrado")
            return False
        
        # Procesar según tipo de archivo
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            success = process_pdf_with_ocr(file_path, job_id)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
            # Procesar imagen directamente
            output_file = RESULT_DIR / f"{job_id}.txt"
            success = process_image_with_tesseract(file_path, output_file.with_suffix(''))
        else:
            logging.error(f"Formato no soportado: {file_ext}")
            update_job_status(job_id, "failed", f"Formato no soportado: {file_ext}")
            return False
        
        # Actualizar estado final
        if success:
            update_job_status(job_id, "completed")
            # Limpiar archivo original
            file_path.unlink(missing_ok=True)
            logging.info(f"Trabajo completado: {job_id}")
            return True
        else:
            update_job_status(job_id, "failed", "Error en procesamiento")
            logging.error(f"Trabajo falló: {job_id}")
            return False
            
    except Exception as e:
        logging.error(f"Error procesando trabajo {job_id}: {e}")
        update_job_status(job_id, "failed", str(e))
        return False

def main_loop():
    logging.info("Esperando trabajos en la cola 'ocr_queue'...")
    
    while True:
        try:
            # Obtener trabajo de la cola (bloqueante, timeout 30 segundos)
            # Usamos BRPOP para obtener y remover de la cola
            result = redis_client.brpop("ocr_queue", timeout=30)
            
            if result:
                # result es una tupla: (queue_name, job_id)
                _, job_id = result
                logging.info(f"Nuevo trabajo obtenido: {job_id}")
                
                # Procesar el trabajo
                process_job(job_id)
            else:
                # Timeout, no hay trabajos
                logging.debug("No hay trabajos en cola, esperando...")
                
        except KeyboardInterrupt:
            logging.info("Worker detenido por usuario")
            break
        except Exception as e:
            logging.error(f"Error en loop principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        # Verificar conexión a Redis
        redis_client.ping()
        logging.info("Conexión a Redis establecida")
        main_loop()
    except redis.ConnectionError:
        logging.error("No se pudo conectar a Redis. Verifica que el servicio esté corriendo.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error fatal: {e}")
        sys.exit(1)