#!/usr/bin/env bash
# ============================================================
# setup.sh — Instalación del entorno en Raspberry Pi 4
# Honeypot FV con Detección por ML
# Universidad Santo Tomás — Ingeniería Electrónica
#
# Sistema operativo: Ubuntu 24.04 LTS (arm64)
# Uso: bash scripts/setup.sh
# ============================================================

set -euo pipefail

AMARILLO='\033[1;33m'
VERDE='\033[0;32m'
ROJO='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${AMARILLO}[SETUP]${NC} $1"; }
ok()    { echo -e "${VERDE}[OK]${NC} $1"; }
error() { echo -e "${ROJO}[ERROR]${NC} $1"; exit 1; }

# ------------------------------------------------------------
# 0. Verificaciones previas
# ------------------------------------------------------------
info "Verificando sistema..."

[[ "$(id -u)" -eq 0 ]] && error "No ejecutar como root. Usar usuario normal con sudo."

if ! command -v docker &>/dev/null; then
    info "Docker no encontrado. Instalando..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    ok "Docker instalado. Reinicia la sesión y vuelve a ejecutar el script."
    exit 0
fi

ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"

if ! docker compose version &>/dev/null; then
    error "Docker Compose v2 no disponible. Actualizar Docker."
fi
ok "Docker Compose $(docker compose version --short)"

# ------------------------------------------------------------
# 1. Actualizar sistema
# ------------------------------------------------------------
info "Actualizando paquetes del sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    tcpdump git curl wget \
    libpcap-dev net-tools

ok "Paquetes del sistema instalados"

# ------------------------------------------------------------
# 2. Entorno virtual Python
# ------------------------------------------------------------
info "Creando entorno virtual Python..."
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

info "Instalando dependencias Python..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
ok "Dependencias Python instaladas en .venv/"

# ------------------------------------------------------------
# 3. Crear carpetas de capturas (persisten fuera de Docker)
# ------------------------------------------------------------
info "Creando carpetas de capturas..."
mkdir -p honeypot/capturas/{cowrie,modbus,mqtt,pcap}
mkdir -p datos/{raw,procesados,etiquetados}
chmod 755 honeypot/capturas/pcap
ok "Carpetas de capturas listas"

# ------------------------------------------------------------
# 4. Permisos para captura de red (tcpdump sin root)
# ------------------------------------------------------------
info "Configurando permisos de tcpdump..."
sudo setcap cap_net_raw,cap_net_admin=eip "$(which tcpdump)" 2>/dev/null || \
    info "No se pudo setcap — tcpdump requerirá sudo en uso directo"
ok "Permisos de red configurados"

# ------------------------------------------------------------
# 5. Redirigir puerto 22 → 2222 para Cowrie (sin root en Docker)
# ------------------------------------------------------------
info "Configurando redirección de puertos para SSH honeypot..."
sudo iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222 2>/dev/null || \
    info "iptables no disponible — configurar redirección manualmente"

# Hacer la regla persistente
if command -v iptables-save &>/dev/null; then
    sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null 2>/dev/null || true
fi
ok "Redirección de puertos configurada"

# ------------------------------------------------------------
# 6. Construir imágenes Docker
# ------------------------------------------------------------
info "Construyendo imágenes Docker (puede tardar varios minutos)..."
docker compose build --quiet
ok "Imágenes Docker construidas"

# ------------------------------------------------------------
# 7. Verificación final
# ------------------------------------------------------------
echo ""
echo -e "${VERDE}============================================================${NC}"
echo -e "${VERDE}  Instalación completada${NC}"
echo -e "${VERDE}============================================================${NC}"
echo ""
echo "  Para iniciar el sistema:"
echo "    docker compose up -d"
echo ""
echo "  Para ver logs en tiempo real:"
echo "    docker compose logs -f"
echo ""
echo "  Dashboard disponible en:"
echo "    http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "  Activar entorno Python:"
echo "    source .venv/bin/activate"
echo ""