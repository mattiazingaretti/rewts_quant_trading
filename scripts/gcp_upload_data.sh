#!/bin/bash
# Script per caricare dati su Google Cloud Storage e sincronizzarli con la VM
# Esegui questo script dal tuo COMPUTER LOCALE

set -e

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

# Modifica questi parametri
PROJECT_ID="rewts-llm-rl"
BUCKET_NAME="rewts-llm-rl-data"
REGION="us-central1"
LOCAL_PROJECT_DIR="/Users/m.zingaretti/UNI/Papers"

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
# VERIFICA PREREQUISITI
# =============================================================================

echo ""
echo "============================================================================="
echo "  Upload Dati su Google Cloud Storage"
echo "============================================================================="
echo ""

print_step "Verifica prerequisiti..."

# Verifica gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI non trovato"
    exit 1
fi

# Verifica gsutil
if ! command -v gsutil &> /dev/null; then
    print_error "gsutil non trovato"
    exit 1
fi

# Verifica directory locale
if [ ! -d "$LOCAL_PROJECT_DIR" ]; then
    print_error "Directory progetto non trovata: $LOCAL_PROJECT_DIR"
    exit 1
fi

# Verifica autenticazione
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_error "Non autenticato. Esegui: gcloud auth login"
    exit 1
fi

# Imposta progetto
gcloud config set project "$PROJECT_ID"

print_success "Prerequisiti OK"

# =============================================================================
# CREA BUCKET SE NON ESISTE
# =============================================================================

print_step "Verifica bucket Google Cloud Storage..."

if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
    print_success "Bucket esistente: gs://$BUCKET_NAME"
else
    print_warning "Bucket non trovato. Creazione in corso..."

    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$BUCKET_NAME/"

    # Configura lifecycle per cancellare file temp dopo 30 giorni
    cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 30,
          "matchesPrefix": ["temp/"]
        }
      }
    ]
  }
}
EOF

    gsutil lifecycle set /tmp/lifecycle.json "gs://$BUCKET_NAME/"
    rm /tmp/lifecycle.json

    print_success "Bucket creato: gs://$BUCKET_NAME"
fi

# =============================================================================
# VERIFICA DIMENSIONE DATI
# =============================================================================

print_step "Calcolo dimensione dati..."

cd "$LOCAL_PROJECT_DIR"

# Calcola dimensione delle directory principali
echo ""
echo "Dimensioni directory:"
du -sh data/ src/ scripts/ 2>/dev/null || true
echo ""

TOTAL_SIZE=$(du -sh . | awk '{print $1}')
print_info "Dimensione totale progetto: $TOTAL_SIZE"
echo ""

read -p "Procedere con l'upload? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Upload annullato"
    exit 0
fi

# =============================================================================
# UPLOAD FILES
# =============================================================================

print_step "Upload files su Cloud Storage..."

# Funzione per upload con progress
upload_dir() {
    local dir=$1
    local desc=$2

    if [ -d "$dir" ]; then
        print_info "Upload $desc..."
        gsutil -m rsync -r -x ".*\.pyc$|.*__pycache__.*|.*\.git.*|.*venv.*" \
            "$dir" "gs://$BUCKET_NAME/$dir"
        print_success "$desc caricato"
    else
        print_warning "$desc non trovato, skip"
    fi
}

# Upload directory principali
echo ""
upload_dir "data" "Dati"
upload_dir "src" "Codice sorgente"
upload_dir "scripts" "Scripts"
upload_dir "configs" "Configurazioni"

# Upload file singoli importanti
print_info "Upload file configurazione..."
gsutil cp requirements.txt "gs://$BUCKET_NAME/" 2>/dev/null || print_warning "requirements.txt non trovato"
gsutil cp README.md "gs://$BUCKET_NAME/" 2>/dev/null || print_warning "README.md non trovato"

# Upload .env se esiste (ATTENZIONE: contiene secrets!)
if [ -f ".env" ]; then
    print_warning ".env trovato"
    read -p "Caricare .env con API keys? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Imposta permessi privati
        gsutil cp .env "gs://$BUCKET_NAME/.env"
        gsutil acl ch -u AllUsers:R "gs://$BUCKET_NAME/.env" 2>/dev/null || true
        print_success ".env caricato (visibile solo a te)"
    fi
fi

print_success "Upload completato!"

# =============================================================================
# VERIFICA UPLOAD
# =============================================================================

print_step "Verifica upload..."

echo ""
echo "Files nel bucket:"
gsutil ls -lh "gs://$BUCKET_NAME/" | head -20

TOTAL_OBJECTS=$(gsutil ls -r "gs://$BUCKET_NAME/**" | wc -l)
print_info "Totale oggetti caricati: $TOTAL_OBJECTS"

# =============================================================================
# DOWNLOAD SU VM
# =============================================================================

echo ""
print_step "Prossimo passo: Download sulla VM"
echo ""
echo "Connettiti alla VM ed esegui:"
echo ""
echo "  cd ~/rewts-project"
echo "  gsutil -m rsync -r gs://$BUCKET_NAME/ ."
echo ""
echo "Oppure esegui questo comando dal tuo computer:"
echo ""
VM_NAME="rewts-training-vm"
ZONE="us-central1-a"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd ~/rewts-project && gsutil -m rsync -r gs://$BUCKET_NAME/ .'"
echo ""

# =============================================================================
# STIMA COSTI STORAGE
# =============================================================================

echo "============================================================================="
echo "STIMA COSTI STORAGE"
echo "============================================================================="
echo ""

# Calcola costi approssimativi
BUCKET_SIZE=$(gsutil du -s "gs://$BUCKET_NAME" | awk '{print $1}')
BUCKET_SIZE_GB=$(echo "scale=2; $BUCKET_SIZE / 1024 / 1024 / 1024" | bc)

echo "Dati nel bucket: ${BUCKET_SIZE_GB} GB"
echo ""
echo "Costi stimati (us-central1):"
STORAGE_COST=$(echo "scale=2; $BUCKET_SIZE_GB * 0.020" | bc)
echo "  Storage:     \$${STORAGE_COST}/mese (\$0.020/GB)"
echo "  Operazioni:  Trascurabili per uso normale"
echo ""
print_info "I dati rimangono nel bucket fino a eliminazione manuale"
echo ""

# =============================================================================
# COMANDI UTILI
# =============================================================================

echo "============================================================================="
echo "COMANDI UTILI"
echo "============================================================================="
echo ""
echo "Visualizza contenuto bucket:"
echo "  gsutil ls -r gs://$BUCKET_NAME/"
echo ""
echo "Download singola directory:"
echo "  gsutil -m cp -r gs://$BUCKET_NAME/data/ ."
echo ""
echo "Elimina file dal bucket:"
echo "  gsutil rm gs://$BUCKET_NAME/path/to/file"
echo ""
echo "Svuota bucket (ATTENZIONE!):"
echo "  gsutil -m rm -r gs://$BUCKET_NAME/**"
echo ""
echo "Elimina bucket:"
echo "  gsutil rb gs://$BUCKET_NAME"
echo ""
echo "============================================================================="
echo ""

print_success "Upload completato con successo!"
