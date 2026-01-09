#!/bin/bash

# setup.sh - Script de configuración para solsticio-infra
# Este script crea todas las carpetas necesarias para el stack
# Uso: ./setup.sh [usuario]

set -e  # Detener ejecución en caso de error

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en /srv
if [[ $(pwd) != "/srv" ]]; then
    print_error "Este script debe ejecutarse desde /srv"
    print_error "Ejecuta: cd /srv && ./setup.sh"
    exit 1
fi

# Obtener usuario (argumento o usuario actual)
if [[ $# -eq 1 ]]; then
    USERNAME="$1"
else
    USERNAME=$(whoami)
    print_warning "No se especificó usuario, usando: $USERNAME"
fi

print_info "Configurando directorios para solsticio-infra..."
print_info "Usuario: $USERNAME"
echo ""

# Crear directorios de datos
print_info "Creando directorios de datos..."
mkdir -p data/ocr/uploads
mkdir -p data/ocr/results
mkdir -p data/redis
mkdir -p data/logs/infra-api
mkdir -p data/logs/infra-ui
mkdir -p data/logs/ocr

# Crear directorio de backups
print_info "Creando directorio de backups..."
mkdir -p backups

print_success "Directorios creados correctamente"
echo ""

# Mostrar estructura creada
print_info "Estructura creada:"
tree -d -L 3 data/ backups/ 2>/dev/null || echo "data/"
echo ""

# Configurar permisos
print_info "Configurando permisos para usuario $USERNAME..."

# Verificar si necesitamos sudo
if [[ $USERNAME != $(whoami) ]] || [[ -w stacks ]] || [[ -w data ]] || [[ -w backups ]]; then
    print_warning "Algunos directorios requieren permisos de superusuario"
    
    # Solicitar contraseña solo si es necesario
    sudo chown -R "$USERNAME:$USERNAME" stacks/ 2>/dev/null || true
    sudo chown -R "$USERNAME:$USERNAME" data/ 2>/dev/null || true
    sudo chown -R "$USERNAME:$USERNAME" backups/ 2>/dev/null || true
    
    print_success "Permisos configurados con sudo"
else
    chown -R "$USERNAME:$USERNAME" stacks/ 2>/dev/null || true
    chown -R "$USERNAME:$USERNAME" data/ 2>/dev/null || true
    chown -R "$USERNAME:$USERNAME" backups/ 2>/dev/null || true
    print_success "Permisos configurados"
fi
echo ""

# Verificación final
print_info "Verificando estructura..."
if [[ -d data/ocr/uploads ]] && [[ -d data/ocr/results ]] && \
   [[ -d data/redis ]] && [[ -d backups ]]; then
    print_success "✓ Todos los directorios fueron creados exitosamente"
else
    print_error "Algunos directorios no pudieron crearse"
    exit 1
fi

echo ""
print_info "Siguientes pasos:"
echo "1. Configura las variables de entorno en .env (ver .env.example)"
echo "2. Configura INFRA_API_TOKEN en stacks/infra-ui/src/config.js"
echo "3. Ejecuta los pasos de instalación con uv"
echo "4. Despliega con: cd stacks/infra && docker compose up -d"
echo ""
print_success "Setup completado exitosamente!"