#!/bin/bash
# Script per configurare l'ambiente sulla VM Google Cloud
# Esegui questo script SULLA VM dopo esserti connesso

set -e

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

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

PROJECT_DIR="$HOME/rewts-project"
VENV_DIR="$HOME/venv_rewts"

# =============================================================================
# VERIFICA PREREQUISITI
# =============================================================================

echo ""
echo "============================================================================="
echo "  Setup Ambiente ReWTS-LLM-RL su Google Cloud VM"
echo "============================================================================="
echo ""

print_step "Verifica prerequisiti..."

# Verifica CUDA/GPU
if ! command -v nvidia-smi &> /dev/null; then
    print_warning "nvidia-smi non trovato. GPU potrebbe non essere configurata."
    echo "Attendi qualche minuto dopo la creazione della VM per l'installazione driver."
    read -p "Vuoi continuare comunque? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "GPU rilevata"
    nvidia-smi --query-gpu=gpu_name,driver_version,memory.total --format=csv
fi

# Verifica Python
if ! command -v python3 &> /dev/null; then
    print_warning "Python3 non trovato. Installazione in corso..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 --version)
print_success "Python: $PYTHON_VERSION"

# =============================================================================
# AGGIORNAMENTO SISTEMA
# =============================================================================

print_step "Aggiornamento sistema..."

sudo apt-get update
sudo apt-get upgrade -y

# Installa utilities utili
sudo apt-get install -y \
    git \
    wget \
    curl \
    vim \
    htop \
    tmux \
    screen \
    zip \
    unzip \
    tree

print_success "Sistema aggiornato"

# =============================================================================
# CREA DIRECTORY PROGETTO
# =============================================================================

print_step "Configurazione directory progetto..."

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

print_success "Directory progetto: $PROJECT_DIR"

# =============================================================================
# AMBIENTE VIRTUALE PYTHON
# =============================================================================

print_step "Creazione ambiente virtuale Python..."

if [ -d "$VENV_DIR" ]; then
    print_warning "Ambiente virtuale già esiste. Rimuovo e ricreo..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Aggiorna pip
pip install --upgrade pip setuptools wheel

print_success "Ambiente virtuale creato: $VENV_DIR"

# =============================================================================
# VERIFICA PYTORCH + CUDA
# =============================================================================

print_step "Verifica PyTorch e CUDA..."

# Su Deep Learning VM, PyTorch dovrebbe già essere installato
if python -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python -c "import torch; print(torch.__version__)")
    CUDA_AVAILABLE=$(python -c "import torch; print(torch.cuda.is_available())")

    print_success "PyTorch: $TORCH_VERSION"

    if [ "$CUDA_AVAILABLE" = "True" ]; then
        CUDA_VERSION=$(python -c "import torch; print(torch.version.cuda)")
        GPU_NAME=$(python -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null || echo "Unknown")
        print_success "CUDA: $CUDA_VERSION"
        print_success "GPU: $GPU_NAME"
    else
        print_warning "CUDA non disponibile in PyTorch"
    fi
else
    print_warning "PyTorch non trovato. Sarà installato dalle requirements."
fi

# =============================================================================
# CONFIGURAZIONE .BASHRC
# =============================================================================

print_step "Configurazione .bashrc..."

# Aggiungi alias e shortcuts utili
cat >> ~/.bashrc << 'EOF'

# ReWTS-LLM-RL shortcuts
alias rewts='cd ~/rewts-project && source ~/venv_rewts/bin/activate'
alias gpu='nvidia-smi'
alias logs='tail -f ~/rewts-project/training.log'

# Attiva automaticamente venv quando entri nella directory
cd() {
    builtin cd "$@"
    if [[ -d ~/venv_rewts ]] && [[ $PWD == ~/rewts-project* ]]; then
        if [[ "$VIRTUAL_ENV" != ~/venv_rewts ]]; then
            source ~/venv_rewts/bin/activate
        fi
    fi
}

EOF

print_success ".bashrc configurato"

# =============================================================================
# SETUP GOOGLE CLOUD STORAGE
# =============================================================================

print_step "Configurazione Google Cloud Storage..."

# gsutil dovrebbe già essere installato su VM GCP
if command -v gsutil &> /dev/null; then
    print_success "gsutil disponibile"

    # Configura gsutil per parallel downloads
    echo "[GSUtil]" > ~/.boto
    echo "parallel_composite_upload_threshold = 150M" >> ~/.boto

    print_info "Buckets disponibili:"
    gsutil ls || print_warning "Nessun bucket trovato o errore di autenticazione"
else
    print_warning "gsutil non trovato"
fi

# =============================================================================
# INFORMAZIONI FINALI
# =============================================================================

echo ""
echo "============================================================================="
print_success "AMBIENTE CONFIGURATO CON SUCCESSO!"
echo "============================================================================="
echo ""
echo "Directory progetto: $PROJECT_DIR"
echo "Ambiente virtuale:  $VENV_DIR"
echo ""
echo "============================================================================="
echo "COMANDI UTILI"
echo "============================================================================="
echo ""
echo "Attiva ambiente virtuale:"
echo "  source ~/venv_rewts/bin/activate"
echo "  # oppure usa alias: rewts"
echo ""
echo "Vai al progetto:"
echo "  cd ~/rewts-project"
echo ""
echo "Monitora GPU:"
echo "  nvidia-smi"
echo "  # oppure: gpu"
echo "  watch -n 1 nvidia-smi  # Auto-refresh"
echo ""
echo "Monitora sistema:"
echo "  htop"
echo ""
echo "============================================================================="
echo "PROSSIMI PASSI"
echo "============================================================================="
echo ""
echo "1. Scarica il codice dal bucket:"
echo "   gsutil -m rsync -r gs://YOUR-BUCKET-NAME/ ~/rewts-project/"
echo ""
echo "2. Installa dipendenze:"
echo "   cd ~/rewts-project"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Configura API keys:"
echo "   export GEMINI_API_KEY='your-key'"
echo "   # oppure crea file .env"
echo ""
echo "4. Verifica configurazione:"
echo "   python scripts/verify_api_keys.py"
echo ""
echo "5. Avvia training:"
echo "   nohup python scripts/train_rewts_llm_rl.py > training.log 2>&1 &"
echo "   # oppure con screen:"
echo "   screen -S training"
echo "   python scripts/train_rewts_llm_rl.py"
echo ""
echo "============================================================================="
echo ""

# Ricarica .bashrc
source ~/.bashrc

print_success "Setup completato! Riavvia la shell o esegui: source ~/.bashrc"
