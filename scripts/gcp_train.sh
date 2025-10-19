#!/bin/bash
# Script per avviare il training sulla VM Google Cloud
# Esegui questo script SULLA VM dopo aver configurato l'ambiente

set -e

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

PROJECT_DIR="$HOME/rewts-project"
VENV_DIR="$HOME/venv_rewts"
TRAINING_SCRIPT="scripts/train_rewts_llm_rl.py"
LOG_FILE="training.log"
BUCKET_NAME="rewts-llm-rl-data"

# =============================================================================
# COLORI
# =============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}➜ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# =============================================================================
# BANNER
# =============================================================================

echo ""
echo "============================================================================="
echo "  ReWTS-LLM-RL Training on Google Cloud"
echo "============================================================================="
echo ""

# =============================================================================
# VERIFICA PREREQUISITI
# =============================================================================

print_step "Verifica prerequisiti..."

# Verifica directory progetto
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Directory progetto non trovata: $PROJECT_DIR"
    print_info "Esegui prima: gsutil -m rsync -r gs://$BUCKET_NAME/ $PROJECT_DIR/"
    exit 1
fi

cd "$PROJECT_DIR"

# Verifica ambiente virtuale
if [ ! -d "$VENV_DIR" ]; then
    print_error "Ambiente virtuale non trovato: $VENV_DIR"
    print_info "Esegui prima: ./scripts/gcp_setup_environment.sh"
    exit 1
fi

# Attiva ambiente virtuale
source "$VENV_DIR/bin/activate"
print_success "Ambiente virtuale attivato"

# Verifica script training
if [ ! -f "$TRAINING_SCRIPT" ]; then
    print_error "Script training non trovato: $TRAINING_SCRIPT"
    exit 1
fi

# Verifica GPU
if ! nvidia-smi &> /dev/null; then
    print_warning "GPU non rilevata!"
    read -p "Continuare senza GPU? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "GPU rilevata"
    nvidia-smi --query-gpu=gpu_name,memory.total --format=csv,noheader
fi

# Verifica dipendenze Python
print_step "Verifica dipendenze Python..."
if python -c "import torch, pandas, google.generativeai" 2>/dev/null; then
    print_success "Dipendenze OK"
else
    print_error "Dipendenze mancanti"
    print_info "Installazione in corso..."
    pip install -r requirements.txt
fi

# Verifica API key
if [ -z "$GEMINI_API_KEY" ]; then
    if [ -f ".env" ]; then
        print_info "Carico API key da .env"
        export $(grep -v '^#' .env | xargs)
    else
        print_error "GEMINI_API_KEY non configurata"
        echo ""
        echo "Configura l'API key in uno dei seguenti modi:"
        echo "  1. export GEMINI_API_KEY='your-key'"
        echo "  2. Crea file .env con: GEMINI_API_KEY=your-key"
        echo ""
        exit 1
    fi
fi

MASKED_KEY="${GEMINI_API_KEY:0:10}...${GEMINI_API_KEY: -4}"
print_success "API key configurata: $MASKED_KEY"

# Verifica dati
print_step "Verifica dati..."
if [ ! -d "data/processed" ]; then
    print_error "Dati non trovati in data/processed"
    exit 1
fi

DATA_FILES=$(ls -1 data/processed/*.csv 2>/dev/null | wc -l)
print_success "$DATA_FILES file CSV trovati"

print_success "Tutti i prerequisiti soddisfatti"

# =============================================================================
# CONFIGURAZIONE TRAINING
# =============================================================================

echo ""
print_step "Configurazione training..."
echo ""

# Chiedi modalità di esecuzione
echo "Come vuoi eseguire il training?"
echo "  1) Foreground (visibile, blocca terminale)"
echo "  2) Background con nohup (continua se disconnetti)"
echo "  3) Screen session (riattaccabile)"
echo "  4) Tmux session (più potente)"
echo ""
read -p "Scegli modalità (1-4): " MODE

# Backup automatico ogni N ore
echo ""
read -p "Abilita backup automatico su Cloud Storage ogni 6h? (y/n) " -n 1 -r
echo
ENABLE_BACKUP=$REPLY

# =============================================================================
# CREA SCRIPT DI BACKUP AUTOMATICO
# =============================================================================

if [[ $ENABLE_BACKUP =~ ^[Yy]$ ]]; then
    print_step "Setup backup automatico..."

    cat > "$HOME/backup_models.sh" << 'BACKUP_EOF'
#!/bin/bash
# Backup automatico modelli su Cloud Storage
PROJECT_DIR="$HOME/rewts-project"
BUCKET="rewts-llm-rl-data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[$(date)] Backup avviato..."

# Backup modelli
if [ -d "$PROJECT_DIR/models" ]; then
    gsutil -m rsync -r "$PROJECT_DIR/models/" "gs://$BUCKET/backups/$TIMESTAMP/models/"
    echo "[$(date)] Modelli backuppati"
fi

# Backup strategie
if [ -d "$PROJECT_DIR/data/llm_strategies" ]; then
    gsutil -m rsync -r "$PROJECT_DIR/data/llm_strategies/" "gs://$BUCKET/backups/$TIMESTAMP/strategies/"
    echo "[$(date)] Strategie backuppate"
fi

# Backup log
if [ -f "$PROJECT_DIR/training.log" ]; then
    gsutil cp "$PROJECT_DIR/training.log" "gs://$BUCKET/logs/training_$TIMESTAMP.log"
    echo "[$(date)] Log backuppato"
fi

echo "[$(date)] Backup completato"
BACKUP_EOF

    chmod +x "$HOME/backup_models.sh"

    # Aggiungi a crontab
    (crontab -l 2>/dev/null; echo "0 */6 * * * $HOME/backup_models.sh >> $HOME/backup.log 2>&1") | crontab -

    print_success "Backup automatico configurato (ogni 6h)"
fi

# =============================================================================
# AVVIA TRAINING
# =============================================================================

echo ""
echo "============================================================================="
print_step "AVVIO TRAINING"
echo "============================================================================="
echo ""

case $MODE in
    1)
        # Foreground
        print_info "Avvio in foreground (premi Ctrl+C per interrompere)"
        sleep 2
        python "$TRAINING_SCRIPT"
        ;;

    2)
        # Background con nohup
        print_info "Avvio in background con nohup"
        nohup python "$TRAINING_SCRIPT" > "$LOG_FILE" 2>&1 &
        PID=$!
        echo $PID > training.pid
        print_success "Training avviato (PID: $PID)"
        echo ""
        echo "Monitora con:"
        echo "  tail -f $LOG_FILE"
        echo "  watch -n 1 nvidia-smi"
        echo ""
        echo "Interrompi con:"
        echo "  kill $PID"
        ;;

    3)
        # Screen
        print_info "Avvio in screen session"

        if command -v screen &> /dev/null; then
            screen -dmS training bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python $TRAINING_SCRIPT"
            print_success "Screen session 'training' avviata"
            echo ""
            echo "Riattacca con:"
            echo "  screen -r training"
            echo ""
            echo "Detach con: Ctrl+A poi D"
            echo "Lista sessions: screen -ls"
        else
            print_error "Screen non installato"
            exit 1
        fi
        ;;

    4)
        # Tmux
        print_info "Avvio in tmux session"

        if command -v tmux &> /dev/null; then
            tmux new-session -d -s training "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python $TRAINING_SCRIPT"
            print_success "Tmux session 'training' avviata"
            echo ""
            echo "Riattacca con:"
            echo "  tmux attach -t training"
            echo ""
            echo "Detach con: Ctrl+B poi D"
            echo "Lista sessions: tmux ls"
        else
            print_error "Tmux non installato"
            exit 1
        fi
        ;;

    *)
        print_error "Modalità non valida"
        exit 1
        ;;
esac

# =============================================================================
# INFORMAZIONI POST-AVVIO
# =============================================================================

echo ""
echo "============================================================================="
print_success "TRAINING AVVIATO"
echo "============================================================================="
echo ""
echo "Directory:     $PROJECT_DIR"
echo "Log file:      $LOG_FILE"
echo "Backup:        $([ "$ENABLE_BACKUP" = "y" ] && echo "Abilitato (ogni 6h)" || echo "Disabilitato")"
echo ""

if [ "$MODE" != "1" ]; then
    echo "============================================================================="
    echo "COMANDI UTILI"
    echo "============================================================================="
    echo ""
    echo "Monitora log in tempo reale:"
    echo "  tail -f $LOG_FILE"
    echo "  tail -f $LOG_FILE | grep -i 'epoch\\|loss\\|reward'"
    echo ""
    echo "Monitora GPU:"
    echo "  watch -n 1 nvidia-smi"
    echo "  nvidia-smi dmon -s u -d 1  # Utilizzo GPU"
    echo ""
    echo "Monitora sistema:"
    echo "  htop"
    echo ""
    echo "Check processi Python:"
    echo "  ps aux | grep python"
    echo ""
    echo "Verifica spazio disco:"
    echo "  df -h"
    echo ""
    echo "============================================================================="
    echo "DISCONNESSIONE SICURA"
    echo "============================================================================="
    echo ""
    echo "Puoi disconnetterti dalla VM in sicurezza:"
    echo "  exit"
    echo ""
    echo "Il training continuerà in background."
    echo ""
    echo "Per riconnetterti:"
    echo "  gcloud compute ssh rewts-training-vm --zone=us-central1-a"
    echo ""
    echo "============================================================================="
fi

echo ""
print_success "Setup completato!"
echo ""

# Mostra le prime righe del log se in background
if [ "$MODE" != "1" ]; then
    sleep 2
    if [ -f "$LOG_FILE" ]; then
        echo "Prime righe del log:"
        echo "---"
        head -20 "$LOG_FILE" 2>/dev/null || echo "(log ancora vuoto)"
        echo "---"
    fi
fi
