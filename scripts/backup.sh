#!/usr/bin/env bash
# ============================================================
# backup.sh — Respaldo de logs, capturas y dataset
# Honeypot FV con Detección por ML
# Universidad Santo Tomás — Ingeniería Electrónica
#
# Uso:
#   bash scripts/backup.sh              # backup completo
#   bash scripts/backup.sh --solo-logs  # solo logs sin PCAPs
#
# Destino por defecto: /media/$USER/backup-honeypot/
# Sobreescribir destino: BACKUP_DEST=/ruta bash scripts/backup.sh
# ============================================================

set -euo pipefail

AMARILLO='\033[1;33m'
VERDE='\033[0;32m'
ROJO='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${AMARILLO}[BACKUP]${NC} $1"; }
ok()    { echo -e "${VERDE}[OK]${NC} $1"; }
error() { echo -e "${ROJO}[ERROR]${NC} $1"; exit 1; }

FECHA=$(date +%Y%m%d_%H%M%S)
SOLO_LOGS=false

for arg in "$@"; do
    [[ "$arg" == "--solo-logs" ]] && SOLO_LOGS=true
done

# Destino: variable de entorno o ruta por defecto
BACKUP_DEST="${BACKUP_DEST:-/media/$USER/backup-honeypot}"
CARPETA_BACKUP="$BACKUP_DEST/backup_$FECHA"

# ------------------------------------------------------------
# Verificar que el destino existe y tiene espacio
# ------------------------------------------------------------
if [[ ! -d "$BACKUP_DEST" ]]; then
    error "Destino de backup no encontrado: $BACKUP_DEST
Conecta el disco externo o define BACKUP_DEST=/ruta antes de ejecutar."
fi

ESPACIO_LIBRE=$(df -BG "$BACKUP_DEST" | awk 'NR==2{print $4}' | tr -d 'G')
if [[ "$ESPACIO_LIBRE" -lt 2 ]]; then
    error "Espacio insuficiente en $BACKUP_DEST (${ESPACIO_LIBRE}G disponibles, mínimo 2G)"
fi

mkdir -p "$CARPETA_BACKUP"
info "Backup iniciado → $CARPETA_BACKUP"

# ------------------------------------------------------------
# 1. Logs estructurados de Cowrie (JSON)
# ------------------------------------------------------------
info "Respaldando logs de Cowrie..."
if [[ -d "honeypot/capturas/cowrie" ]]; then
    rsync -a --include="*.json" --include="*.json.gz" --exclude="*" \
        honeypot/capturas/cowrie/ "$CARPETA_BACKUP/cowrie/"
    ok "Logs Cowrie: $(find "$CARPETA_BACKUP/cowrie" -type f | wc -l) archivos"
else
    info "Sin logs de Cowrie aún"
fi

# ------------------------------------------------------------
# 2. Logs de Modbus y MQTT
# ------------------------------------------------------------
info "Respaldando logs de Modbus y MQTT..."
for servicio in modbus mqtt; do
    if [[ -d "honeypot/capturas/$servicio" ]]; then
        rsync -a honeypot/capturas/$servicio/ "$CARPETA_BACKUP/$servicio/"
        ok "Logs $servicio copiados"
    fi
done

# ------------------------------------------------------------
# 3. Archivos PCAP (omitir con --solo-logs)
# ------------------------------------------------------------
if [[ "$SOLO_LOGS" == false ]]; then
    info "Respaldando capturas PCAP..."
    if [[ -d "honeypot/capturas/pcap" ]]; then
        rsync -a --include="*.pcap" --include="*.pcap.gz" --exclude="*" \
            honeypot/capturas/pcap/ "$CARPETA_BACKUP/pcap/"
        TOTAL_PCAP=$(du -sh "$CARPETA_BACKUP/pcap" 2>/dev/null | cut -f1 || echo "0")
        ok "PCAPs: $TOTAL_PCAP copiados"
    else
        info "Sin PCAPs aún"
    fi
else
    info "Omitiendo PCAPs (--solo-logs activo)"
fi

# ------------------------------------------------------------
# 4. Dataset procesado y etiquetado
# ------------------------------------------------------------
info "Respaldando dataset..."
for carpeta in datos/procesados datos/etiquetados; do
    if [[ -d "$carpeta" ]] && [[ -n "$(ls -A "$carpeta" 2>/dev/null)" ]]; then
        rsync -a "$carpeta/" "$CARPETA_BACKUP/$(basename $carpeta)/"
        ok "$(basename $carpeta): $(find "$CARPETA_BACKUP/$(basename $carpeta)" -type f | wc -l) archivos"
    fi
done

# ------------------------------------------------------------
# 5. Modelos ML entrenados
# ------------------------------------------------------------
info "Respaldando modelos ML..."
if [[ -d "ml/modelos" ]] && [[ -n "$(ls -A ml/modelos 2>/dev/null)" ]]; then
    rsync -a ml/modelos/ "$CARPETA_BACKUP/modelos/"
    ok "Modelos copiados: $(ls ml/modelos/*.pkl 2>/dev/null | wc -l) archivos .pkl"
fi

# ------------------------------------------------------------
# 6. Manifiesto del backup
# ------------------------------------------------------------
MANIFIESTO="$CARPETA_BACKUP/MANIFIESTO.txt"
{
    echo "Backup generado: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Hostname: $(hostname)"
    echo "Usuario: $USER"
    echo "Proyecto: tesis-honeypot-fv-ml"
    echo ""
    echo "Contenido:"
    find "$CARPETA_BACKUP" -type f | sort | sed "s|$CARPETA_BACKUP/||"
    echo ""
    echo "Tamaño total:"
    du -sh "$CARPETA_BACKUP"
} > "$MANIFIESTO"

# ------------------------------------------------------------
# Resumen
# ------------------------------------------------------------
TOTAL=$(du -sh "$CARPETA_BACKUP" | cut -f1)
echo ""
echo -e "${VERDE}============================================================${NC}"
echo -e "${VERDE}  Backup completado — $TOTAL${NC}"
echo -e "${VERDE}============================================================${NC}"
echo "  Destino: $CARPETA_BACKUP"
echo "  Manifiesto: $MANIFIESTO"
echo ""