#!/bin/bash
# Script per creare VM Google Cloud con GPU per training ReWTS-LLM-RL

set -e  # Exit on error

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

# Modifica questi parametri secondo le tue esigenze
PROJECT_ID="rewts-llm-rl"
VM_NAME="rewts-training-vm"
ZONE="us-central1-a"
REGION="us-central1"

# Configurazione Hardware
MACHINE_TYPE="n1-standard-4"     # 4 vCPU, 15 GB RAM
GPU_TYPE="nvidia-tesla-t4"       # T4 GPU
GPU_COUNT="1"
BOOT_DISK_SIZE="100GB"
BOOT_DISK_TYPE="pd-standard"

# Immagine Deep Learning (include CUDA, PyTorch, ecc.)
IMAGE_FAMILY="common-cu118-debian-11-py310"
IMAGE_PROJECT="deeplearning-platform-release"

# Opzioni
PREEMPTIBLE="false"  # Cambia a "true" per VM preemptible (più economica ma interrompibile)

# =============================================================================
# COLORI PER OUTPUT
# =============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# =============================================================================
# FUNZIONI
# =============================================================================

print_step() {
    echo -e "${GREEN}➜ $1${NC}"
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

print_step "Verifica prerequisiti..."

# Verifica gcloud installato
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI non trovato. Installa da: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verifica autenticazione
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_error "Non sei autenticato. Esegui: gcloud auth login"
    exit 1
fi

print_success "Prerequisiti OK"

# =============================================================================
# SETUP PROGETTO
# =============================================================================

print_step "Setup progetto ${PROJECT_ID}..."

# Verifica se il progetto esiste
if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    print_warning "Progetto non trovato. Creazione in corso..."
    gcloud projects create "$PROJECT_ID" --name="ReWTS-LLM-RL Training"
fi

# Imposta progetto corrente
gcloud config set project "$PROJECT_ID"
print_success "Progetto configurato"

# =============================================================================
# ABILITA API
# =============================================================================

print_step "Abilitazione API necessarie..."

gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com

print_success "API abilitate"

# =============================================================================
# VERIFICA QUOTA GPU
# =============================================================================

print_step "Verifica quota GPU..."

# Prova a verificare la quota (questo è indicativo)
print_warning "Se ricevi errori sulla quota GPU, segui questi passi:"
echo "  1. Vai su: https://console.cloud.google.com/iam-admin/quotas"
echo "  2. Filtra per 'GPUs (all regions)'"
echo "  3. Richiedi aumento quota se necessario"
echo ""
read -p "Premi ENTER per continuare o CTRL+C per annullare..."

# =============================================================================
# CREA VM
# =============================================================================

print_step "Creazione VM ${VM_NAME}..."

# Costruisci comando
CREATE_CMD="gcloud compute instances create ${VM_NAME} \
  --project=${PROJECT_ID} \
  --zone=${ZONE} \
  --machine-type=${MACHINE_TYPE} \
  --accelerator=type=${GPU_TYPE},count=${GPU_COUNT} \
  --image-family=${IMAGE_FAMILY} \
  --image-project=${IMAGE_PROJECT} \
  --boot-disk-size=${BOOT_DISK_SIZE} \
  --boot-disk-type=${BOOT_DISK_TYPE} \
  --boot-disk-device-name=${VM_NAME} \
  --maintenance-policy=TERMINATE \
  --metadata='install-nvidia-driver=True' \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --tags=http-server,https-server"

# Aggiungi flag preemptible se richiesto
if [ "$PREEMPTIBLE" = "true" ]; then
    CREATE_CMD="$CREATE_CMD --preemptible"
    print_warning "Creazione VM PREEMPTIBLE (più economica ma interrompibile)"
fi

# Esegui creazione
if eval "$CREATE_CMD"; then
    print_success "VM creata con successo!"
else
    print_error "Errore nella creazione della VM"
    exit 1
fi

# =============================================================================
# ATTENDI AVVIO
# =============================================================================

print_step "Attendi che la VM sia pronta..."
sleep 30

# Verifica che la VM sia running
VM_STATUS=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)")
if [ "$VM_STATUS" = "RUNNING" ]; then
    print_success "VM in esecuzione"
else
    print_warning "VM status: $VM_STATUS"
fi

# =============================================================================
# CREA REGOLE FIREWALL
# =============================================================================

print_step "Configurazione firewall..."

# Regola per HTTP (opzionale, per Jupyter/dashboard)
if ! gcloud compute firewall-rules describe allow-http &> /dev/null; then
    gcloud compute firewall-rules create allow-http \
        --allow=tcp:80 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=http-server \
        --description="Allow HTTP traffic"
fi

# Regola per HTTPS
if ! gcloud compute firewall-rules describe allow-https &> /dev/null; then
    gcloud compute firewall-rules create allow-https \
        --allow=tcp:443 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=https-server \
        --description="Allow HTTPS traffic"
fi

print_success "Firewall configurato"

# =============================================================================
# INFORMAZIONI VM
# =============================================================================

echo ""
echo "============================================================================="
print_success "VM CREATA CON SUCCESSO!"
echo "============================================================================="
echo ""
echo "Nome VM:        $VM_NAME"
echo "Zone:           $ZONE"
echo "Machine Type:   $MACHINE_TYPE"
echo "GPU:            $GPU_COUNT x $GPU_TYPE"
echo "Disk:           $BOOT_DISK_SIZE"
echo "Preemptible:    $PREEMPTIBLE"
echo ""

# IP esterno
EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
echo "IP Esterno:     $EXTERNAL_IP"
echo ""

# Stima costi
echo "============================================================================="
echo "STIMA COSTI"
echo "============================================================================="
if [ "$PREEMPTIBLE" = "true" ]; then
    echo "Costo stimato:  ~\$0.20/ora (preemptible)"
else
    echo "Costo stimato:  ~\$0.65/ora"
fi
echo "Costo/giorno:   ~\$15.60 (se lasciata accesa 24h)"
echo ""
echo "⚠ RICORDA: Ferma la VM quando non in uso per evitare costi!"
echo "   gcloud compute instances stop $VM_NAME --zone=$ZONE"
echo ""

# =============================================================================
# PROSSIMI PASSI
# =============================================================================

echo "============================================================================="
echo "PROSSIMI PASSI"
echo "============================================================================="
echo ""
echo "1. Connettiti alla VM:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "2. Verifica GPU:"
echo "   nvidia-smi"
echo ""
echo "3. Esegui setup ambiente:"
echo "   ./scripts/gcp_setup_environment.sh"
echo ""
echo "4. Trasferisci dati:"
echo "   ./scripts/gcp_upload_data.sh"
echo ""
echo "5. Avvia training:"
echo "   ./scripts/gcp_train.sh"
echo ""
echo "============================================================================="
echo ""

print_success "Setup completato!"
