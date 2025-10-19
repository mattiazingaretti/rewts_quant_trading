# Google Cloud Platform - Quick Start

Setup rapido per il training su Google Cloud Platform in 5 passi.

## 📋 Prerequisiti

- Account Google Cloud ([$300 crediti gratis](https://cloud.google.com/free))
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installato
- Carta di credito per billing

## 🚀 Setup in 5 Passi

### 1. Installa e Autentica gcloud

```bash
# Installa gcloud CLI
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Autentica
gcloud auth login
```

### 2. Crea VM con GPU

```bash
cd /Users/m.zingaretti/UNI/Papers

# Script automatico
./scripts/gcp_create_vm.sh

# Tempo: ~3-5 minuti
# Costo: ~$0.65/ora quando accesa
```

Lo script crea:
- ✓ VM n1-standard-4 (4 CPU, 15 GB RAM)
- ✓ GPU Tesla T4
- ✓ Deep Learning image (CUDA preinstallato)
- ✓ 100 GB storage

### 3. Carica Dati su Cloud Storage

```bash
# Crea bucket e carica dati
./scripts/gcp_upload_data.sh

# Tempo: dipende dalla dimensione dati
# Costo storage: ~$0.02/GB/mese
```

### 4. Setup Ambiente sulla VM

```bash
# Connetti alla VM
gcloud compute ssh rewts-training-vm --zone=us-central1-a

# Sulla VM: scarica script di setup
gsutil cp gs://rewts-llm-rl-data/scripts/gcp_setup_environment.sh .
chmod +x gcp_setup_environment.sh
./gcp_setup_environment.sh

# Scarica progetto
cd ~/rewts-project
gsutil -m rsync -r gs://rewts-llm-rl-data/ .

# Installa dipendenze
source ~/venv_rewts/bin/activate
pip install -r requirements.txt

# Configura API key
export GEMINI_API_KEY='your-key-here'
# oppure
nano .env  # e aggiungi: GEMINI_API_KEY=your-key
```

### 5. Avvia Training

```bash
# Sulla VM
./scripts/gcp_train.sh

# Scegli modalità:
# - Screen (raccomandato): riattaccabile
# - Background: continua se disconnetti
# - Foreground: vedi output diretto

# Disconnetti in sicurezza (training continua)
# Premi Ctrl+A poi D (se screen)
# oppure
exit
```

## 📊 Gestione VM

```bash
# Dal tuo computer locale

# Status
./scripts/gcp_manage_vm.sh status

# Ferma VM (importante per risparmiare!)
./scripts/gcp_manage_vm.sh stop

# Riavvia
./scripts/gcp_manage_vm.sh start

# Connetti
./scripts/gcp_manage_vm.sh ssh

# Scarica risultati
./scripts/gcp_manage_vm.sh download

# Stima costi
./scripts/gcp_manage_vm.sh cost
```

## 💰 Costi

| Risorsa | Costo | Quando |
|---------|-------|--------|
| **VM + GPU** | $0.65/h | Solo quando accesa |
| **Storage** | $4/mese | Sempre (100 GB) |
| **Cloud Storage** | $0.02/GB/mese | Per dati |

### Risparmio:
- ✅ **Ferma VM** quando non in uso → $0/h
- ✅ Usa **preemptible** → -60% costo (ma interrompibile)
- ✅ **Elimina VM** dopo training → solo storage

### Budget Alert:
```bash
# Setup alert via console
https://console.cloud.google.com/billing/budgets

# Imposta:
# - Budget: $100
# - Alert: 50%, 90%, 100%
```

## 📈 Monitoraggio Training

### Dalla VM:

```bash
# Log in tempo reale
tail -f ~/rewts-project/training.log

# GPU usage
watch -n 1 nvidia-smi

# Riattacca session
screen -r training  # se hai usato screen
tmux attach -t training  # se hai usato tmux
```

### Dal tuo computer:

```bash
# Scarica log
./scripts/gcp_manage_vm.sh logs

# Scarica tutto
./scripts/gcp_manage_vm.sh download
```

## 🔧 Troubleshooting

### GPU Quota Exceeded

```bash
# Errore: "Quota 'NVIDIA_T4_GPUS' exceeded"

# Soluzione:
# 1. Vai su: https://console.cloud.google.com/iam-admin/quotas
# 2. Filtra: "GPU"
# 3. Richiedi aumento
# 4. Attendi 24-48h
```

### VM non si avvia

```bash
# Verifica stato
./scripts/gcp_manage_vm.sh status

# Check logs
gcloud compute instances get-serial-port-output rewts-training-vm --zone=us-central1-a
```

### Training si interrompe

```bash
# Riconnetti
gcloud compute ssh rewts-training-vm --zone=us-central1-a

# Verifica processo
ps aux | grep python

# Check log
tail -100 ~/rewts-project/training.log

# Riavvia se necessario
cd ~/rewts-project
source ~/venv_rewts/bin/activate
./scripts/gcp_train.sh
```

## 📚 Risorse Utili

- **Guida Completa:** [`docs/google_cloud_setup_guide.md`](./google_cloud_setup_guide.md)
- **Console GCP:** https://console.cloud.google.com/
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Support:** https://cloud.google.com/support

## ✅ Checklist Completa

Prima del training:
- [ ] gcloud CLI installato e autenticato
- [ ] Progetto GCP creato
- [ ] Billing abilitato
- [ ] Budget alert configurato
- [ ] VM creata con script
- [ ] Dati caricati su Cloud Storage
- [ ] Ambiente configurato sulla VM
- [ ] API key configurata
- [ ] Dipendenze installate

Durante il training:
- [ ] Training avviato in background/screen
- [ ] Monitor GPU funziona
- [ ] Backup automatico configurato (opzionale)
- [ ] Log accessibile

Dopo il training:
- [ ] Risultati scaricati
- [ ] VM fermata (o eliminata)
- [ ] Backup su Cloud Storage verificato
- [ ] Costi controllati

## 🆘 Aiuto

**Problemi?**
1. Controlla i log: `./scripts/gcp_manage_vm.sh logs`
2. Verifica status: `./scripts/gcp_manage_vm.sh status`
3. Leggi guida completa: `docs/google_cloud_setup_guide.md`

**Non dimenticare:**
```bash
# FERMA LA VM QUANDO HAI FINITO!
./scripts/gcp_manage_vm.sh stop
```

---

**Tempo totale setup:** ~15-30 minuti
**Difficoltà:** ⭐⭐⭐ (Intermedia)
**Costo stimato:** $2-5 per training completo
