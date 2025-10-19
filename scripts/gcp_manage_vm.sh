#!/bin/bash
# Script per gestire la VM Google Cloud (start, stop, status, ssh, delete)
# Esegui questo script dal tuo COMPUTER LOCALE

set -e

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

PROJECT_ID="rewts-llm-rl"
VM_NAME="rewts-training-vm"
ZONE="us-central1-a"

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
# FUNZIONI
# =============================================================================

check_vm_exists() {
    if ! gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &> /dev/null; then
        print_error "VM '$VM_NAME' non trovata nella zone $ZONE"
        exit 1
    fi
}

get_vm_status() {
    gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)"
}

get_vm_info() {
    local info=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="table(
        name,
        zone.basename(),
        machineType.basename(),
        status,
        networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP
    )")
    echo "$info"
}

calculate_runtime() {
    local start_time=$1
    local current_time=$(date +%s)
    local runtime=$((current_time - start_time))

    local hours=$((runtime / 3600))
    local minutes=$(((runtime % 3600) / 60))

    echo "${hours}h ${minutes}m"
}

estimate_cost() {
    local runtime_hours=$1
    local cost_per_hour=0.65  # T4 GPU + n1-standard-4

    local total_cost=$(echo "scale=2; $runtime_hours * $cost_per_hour" | bc)
    echo "\$${total_cost}"
}

# =============================================================================
# COMANDI
# =============================================================================

cmd_status() {
    print_step "Stato VM..."
    echo ""

    check_vm_exists

    # Informazioni base
    get_vm_info
    echo ""

    # Stato dettagliato
    local status=$(get_vm_status)

    case $status in
        RUNNING)
            print_success "VM in esecuzione"

            # IP esterno
            local ip=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
            print_info "IP esterno: $ip"

            # Tempo di esecuzione
            local start_time=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(lastStartTimestamp)")
            if [ -n "$start_time" ]; then
                local start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${start_time:0:19}" +%s 2>/dev/null || date -d "${start_time:0:19}" +%s 2>/dev/null)
                if [ -n "$start_epoch" ]; then
                    local runtime=$(calculate_runtime $start_epoch)
                    print_info "Tempo di esecuzione: $runtime"

                    # Stima costi
                    local hours=$(($(date +%s) - start_epoch))
                    hours=$(echo "scale=2; $hours / 3600" | bc)
                    local cost=$(estimate_cost $hours)
                    print_warning "Costo stimato: $cost"
                fi
            fi
            ;;
        TERMINATED)
            print_info "VM fermata"
            ;;
        *)
            print_warning "Stato: $status"
            ;;
    esac

    echo ""
}

cmd_start() {
    print_step "Avvio VM..."

    check_vm_exists

    local status=$(get_vm_status)
    if [ "$status" = "RUNNING" ]; then
        print_warning "VM già in esecuzione"
        return
    fi

    gcloud compute instances start "$VM_NAME" --zone="$ZONE"
    print_success "VM avviata"

    echo ""
    print_info "Attendi ~30 secondi per la connessione SSH..."
    sleep 3
}

cmd_stop() {
    print_step "Arresto VM..."

    check_vm_exists

    local status=$(get_vm_status)
    if [ "$status" = "TERMINATED" ]; then
        print_warning "VM già fermata"
        return
    fi

    print_warning "Stai per fermare la VM"
    read -p "Confermi? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud compute instances stop "$VM_NAME" --zone="$ZONE"
        print_success "VM fermata"
        print_info "I dischi persistenti sono conservati (continuano a costare ~\$0.04/GB/mese)"
    else
        print_info "Annullato"
    fi
}

cmd_restart() {
    print_step "Riavvio VM..."

    cmd_stop
    sleep 5
    cmd_start
}

cmd_ssh() {
    print_step "Connessione SSH..."

    check_vm_exists

    local status=$(get_vm_status)
    if [ "$status" != "RUNNING" ]; then
        print_error "VM non in esecuzione (status: $status)"
        print_info "Avvia prima la VM con: $0 start"
        exit 1
    fi

    print_info "Connessione in corso..."
    gcloud compute ssh "$VM_NAME" --zone="$ZONE"
}

cmd_logs() {
    print_step "Recupero log training..."

    check_vm_exists

    local status=$(get_vm_status)
    if [ "$status" != "RUNNING" ]; then
        print_error "VM non in esecuzione"
        exit 1
    fi

    print_info "Scarico training.log..."
    gcloud compute scp "$VM_NAME:~/rewts-project/training.log" ./training.log --zone="$ZONE" || {
        print_warning "Log non trovato o errore nel download"
        exit 1
    }

    print_success "Log scaricato: ./training.log"
    echo ""
    echo "Ultime 50 righe:"
    echo "---"
    tail -50 ./training.log
    echo "---"
}

cmd_download() {
    print_step "Download modelli e risultati..."

    check_vm_exists

    local status=$(get_vm_status)
    if [ "$status" != "RUNNING" ]; then
        print_error "VM non in esecuzione"
        exit 1
    fi

    # Crea directory locale per download
    local download_dir="./gcp_results_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$download_dir"

    print_info "Download in: $download_dir"

    # Download modelli
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="test -d ~/rewts-project/models" 2>/dev/null; then
        print_info "Download modelli..."
        gcloud compute scp --recurse "$VM_NAME:~/rewts-project/models" "$download_dir/" --zone="$ZONE"
        print_success "Modelli scaricati"
    fi

    # Download strategie
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="test -d ~/rewts-project/data/llm_strategies" 2>/dev/null; then
        print_info "Download strategie..."
        gcloud compute scp --recurse "$VM_NAME:~/rewts-project/data/llm_strategies" "$download_dir/" --zone="$ZONE"
        print_success "Strategie scaricate"
    fi

    # Download log
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="test -f ~/rewts-project/training.log" 2>/dev/null; then
        gcloud compute scp "$VM_NAME:~/rewts-project/training.log" "$download_dir/" --zone="$ZONE"
    fi

    print_success "Download completato in: $download_dir"
}

cmd_delete() {
    print_step "Eliminazione VM..."

    check_vm_exists

    echo ""
    print_warning "ATTENZIONE: Stai per ELIMINARE la VM"
    print_warning "Tutti i dati sulla VM saranno PERSI"
    print_info "I dati in Cloud Storage saranno preservati"
    echo ""
    read -p "Sei SICURO? Digita 'DELETE' per confermare: " confirm

    if [ "$confirm" = "DELETE" ]; then
        # Offri backup prima di eliminare
        read -p "Vuoi fare un backup prima? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cmd_download
        fi

        print_info "Eliminazione in corso..."
        gcloud compute instances delete "$VM_NAME" --zone="$ZONE" --quiet

        print_success "VM eliminata"
        print_info "I dischi sono stati eliminati"
        print_info "I dati in Cloud Storage rimangono disponibili"
    else
        print_info "Eliminazione annullata"
    fi
}

cmd_snapshot() {
    print_step "Creazione snapshot..."

    check_vm_exists

    local snapshot_name="rewts-snapshot-$(date +%Y%m%d-%H%M%S)"

    print_info "Nome snapshot: $snapshot_name"

    gcloud compute disks snapshot "$VM_NAME" \
        --snapshot-names="$snapshot_name" \
        --zone="$ZONE"

    print_success "Snapshot creato: $snapshot_name"
    print_info "Usa questo snapshot per ripristinare o creare nuove VM"
}

cmd_cost() {
    print_step "Stima costi..."

    check_vm_exists

    echo ""
    echo "Configurazione VM:"
    echo "  Machine: n1-standard-4 (~\$0.30/h)"
    echo "  GPU: Tesla T4 (~\$0.35/h)"
    echo "  Totale: ~\$0.65/h"
    echo ""

    local status=$(get_vm_status)
    if [ "$status" = "RUNNING" ]; then
        print_warning "VM in esecuzione"

        local start_time=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(lastStartTimestamp)")
        if [ -n "$start_time" ]; then
            local start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${start_time:0:19}" +%s 2>/dev/null || date -d "${start_time:0:19}" +%s 2>/dev/null)
            if [ -n "$start_epoch" ]; then
                local hours=$(echo "scale=2; ($(date +%s) - $start_epoch) / 3600" | bc)
                local cost=$(echo "scale=2; $hours * 0.65" | bc)

                echo "Sessione corrente:"
                echo "  Durata: $(calculate_runtime $start_epoch)"
                echo "  Costo: \$${cost}"
                echo ""
            fi
        fi
    else
        print_info "VM fermata (nessun costo compute)"
    fi

    # Costi storage
    local disk_size=$(gcloud compute disks describe "$VM_NAME" --zone="$ZONE" --format="value(sizeGb)")
    local storage_cost=$(echo "scale=2; $disk_size * 0.04" | bc)

    echo "Storage (persistente):"
    echo "  Disk size: ${disk_size} GB"
    echo "  Costo/mese: \$${storage_cost}"
    echo ""

    print_info "Per costi dettagliati: https://console.cloud.google.com/billing"
}

# =============================================================================
# MENU E HELP
# =============================================================================

show_usage() {
    cat << EOF
Gestione VM Google Cloud per ReWTS-LLM-RL

Usage: $0 COMMAND

Commands:
  status      Mostra stato della VM
  start       Avvia la VM
  stop        Ferma la VM
  restart     Riavvia la VM
  ssh         Connetti via SSH
  logs        Scarica e mostra log training
  download    Scarica modelli e risultati
  snapshot    Crea snapshot del disco
  delete      Elimina la VM (ATTENZIONE!)
  cost        Stima costi
  help        Mostra questo help

Esempi:
  $0 status        # Verifica stato
  $0 start         # Avvia VM
  $0 ssh           # Connetti
  $0 logs          # Vedi log
  $0 stop          # Ferma per risparmiare

Configurazione:
  Project: $PROJECT_ID
  VM:      $VM_NAME
  Zone:    $ZONE

EOF
}

# =============================================================================
# MAIN
# =============================================================================

# Verifica gcloud installato
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI non trovato"
    echo "Installa da: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Imposta progetto
gcloud config set project "$PROJECT_ID" 2>/dev/null

# Parse command
COMMAND=${1:-help}

case $COMMAND in
    status)
        cmd_status
        ;;
    start)
        cmd_start
        cmd_status
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    ssh)
        cmd_ssh
        ;;
    logs)
        cmd_logs
        ;;
    download)
        cmd_download
        ;;
    snapshot)
        cmd_snapshot
        ;;
    delete)
        cmd_delete
        ;;
    cost)
        cmd_cost
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Comando non riconosciuto: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac
