# Guida Completa: Training su Google Cloud Platform

Questa guida ti aiuta a configurare e eseguire il training del sistema ReWTS-LLM-RL su Google Cloud Platform (GCP).

## 📋 Indice

1. [Vantaggi di Google Cloud vs Colab](#vantaggi)
2. [Setup Iniziale](#setup-iniziale)
3. [Creazione VM con GPU](#creazione-vm)
4. [Configurazione Ambiente](#configurazione-ambiente)
5. [Trasferimento Dati](#trasferimento-dati)
6. [Esecuzione Training](#esecuzione-training)
7. [Gestione Costi](#gestione-costi)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Vantaggi di Google Cloud vs Colab {#vantaggi}

| Caratteristica | Colab Free | Colab Pro | Google Cloud |
|----------------|------------|-----------|--------------|
| **GPU disponibili** | T4 | T4/V100 | T4/V100/A100/H100 |
| **Limite sessione** | 12h | 24h | ∞ Illimitato |
| **Persistenza** | No | No | ✅ Sì |
| **RAM** | 12-16 GB | 32 GB | Configurabile |
| **Storage** | 15 GB | 100 GB | Configurabile |
| **Costo** | Gratis | $10/mese | Pay-as-you-go |
| **Controllo** | Limitato | Limitato | ✅ Completo |
| **SSH/Terminal** | ❌ No | ❌ No | ✅ Sì |
| **Background jobs** | ❌ No | ❌ No | ✅ Sì |

### Quando usare Google Cloud:
- ✅ Training lunghi (>12h)
- ✅ Serve GPU potente (A100)
- ✅ Serve controllo completo
- ✅ Training multipli in parallelo
- ✅ Produzione/deployment

---

## 🚀 Setup Iniziale {#setup-iniziale}

### 1. Account Google Cloud

1. **Vai su:** https://cloud.google.com/
2. **Clicca:** "Get started for free"
3. **Crediti gratis:** $300 per 90 giorni (per nuovi utenti)

### 2. Crea un Progetto

```bash
# Via web console
1. Vai su: https://console.cloud.google.com/
2. Clicca sul menu progetti in alto
3. "New Project" > Nome: "rewts-llm-rl" > Create

# Via gcloud CLI (locale)
gcloud projects create rewts-llm-rl --name="ReWTS-LLM-RL Training"
gcloud config set project rewts-llm-rl
```

### 3. Abilita Billing

1. Vai su: **Billing** nel menu
2. Collega carta di credito
3. **IMPORTANTE:** Imposta budget alerts!

### 4. Abilita API necessarie

```bash
# Via console web
Navigation menu > APIs & Services > Enable APIs and Services

# Cerca e abilita:
- Compute Engine API
- Cloud Storage API
- Cloud Logging API

# Via gcloud CLI
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
```

### 5. Installa Google Cloud SDK (sul tuo computer)

```bash
# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Oppure con brew
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download da: https://cloud.google.com/sdk/docs/install
```

### 6. Autentica

```bash
gcloud auth login
gcloud config set project rewts-llm-rl
```

---

## 🖥️ Creazione VM con GPU {#creazione-vm}

### Opzione 1: Via Console Web (Raccomandato per principianti)

1. **Vai su:** https://console.cloud.google.com/compute/instances
2. **Clicca:** "Create Instance"
3. **Configura:**

```
Nome: rewts-training-vm
Region: us-central1 (a)
Zone: us-central1-a

Machine Configuration:
  Series: N1
  Machine type: n1-standard-4 (4 vCPU, 15 GB RAM)

GPU:
  Clicca "ADD GPU"
  GPU type: NVIDIA Tesla T4
  Number of GPUs: 1

Boot disk:
  Clicca "Change"
  Operating System: Deep Learning on Linux
  Version: Deep Learning VM with CUDA 11.8 M118
  Boot disk type: Standard persistent disk
  Size: 100 GB

Firewall:
  ✅ Allow HTTP traffic
  ✅ Allow HTTPS traffic
```

4. **Clicca:** "Create"

### Opzione 2: Via gcloud CLI (Più veloce)

Usa lo script che creerò nella prossima sezione.

### Costi Stimati

| Configurazione | GPU | Costo/ora | Costo/giorno (24h) |
|----------------|-----|-----------|-------------------|
| n1-standard-4 + T4 | T4 | ~$0.65/h | ~$15.6 |
| n1-standard-8 + T4 | T4 | ~$0.85/h | ~$20.4 |
| a2-highgpu-1g | A100 | ~$3.67/h | ~$88 |

**Suggerimento:** Usa T4 per iniziare. È economica e sufficiente per il training.

---

## ⚙️ Configurazione Ambiente {#configurazione-ambiente}

### 1. Connettiti alla VM

```bash
# Via gcloud CLI
gcloud compute ssh rewts-training-vm --zone=us-central1-a

# Oppure via console web
# Vai su: Compute Engine > VM instances > SSH
```

### 2. Verifica GPU

```bash
# Verifica che CUDA sia installato
nvidia-smi

# Dovresti vedere:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.xx.xx    Driver Version: 525.xx.xx    CUDA Version: 11.8    |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  Tesla T4            Off  | 00000000:00:04.0 Off |                    0 |
# | N/A   43C    P0    26W /  70W |      0MiB / 15109MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

### 3. Setup Ambiente Python

Lo script di setup (che creerò) farà tutto automaticamente, oppure manualmente:

```bash
# Aggiorna sistema
sudo apt-get update
sudo apt-get upgrade -y

# Python e pip dovrebbero già essere installati con Deep Learning VM
python3 --version
pip3 --version

# Crea ambiente virtuale
python3 -m venv ~/venv_rewts
source ~/venv_rewts/bin/activate

# Aggiorna pip
pip install --upgrade pip
```

---

## 📦 Trasferimento Dati {#trasferimento-dati}

### Metodo 1: Google Cloud Storage (Raccomandato)

#### Passo 1: Crea bucket su Cloud Storage

```bash
# Sul tuo computer locale
PROJECT_ID=$(gcloud config get-value project)
BUCKET_NAME="rewts-llm-rl-data"

# Crea bucket
gsutil mb -p $PROJECT_ID -l us-central1 gs://$BUCKET_NAME/

# Verifica
gsutil ls
```

#### Passo 2: Carica dati dal tuo computer

```bash
# Dal tuo computer locale, nella directory Papers/
cd /Users/m.zingaretti/UNI/Papers

# Carica tutto il progetto
gsutil -m rsync -r . gs://$BUCKET_NAME/

# Oppure carica solo dati e codice
gsutil -m cp -r data/ gs://$BUCKET_NAME/data/
gsutil -m cp -r src/ gs://$BUCKET_NAME/src/
gsutil -m cp -r scripts/ gs://$BUCKET_NAME/scripts/
gsutil -m cp requirements.txt gs://$BUCKET_NAME/
gsutil -m cp .env gs://$BUCKET_NAME/  # Se usi .env per API keys

# Verifica upload
gsutil ls -r gs://$BUCKET_NAME/
```

#### Passo 3: Scarica sulla VM

```bash
# Sulla VM
cd ~
mkdir -p rewts-project
cd rewts-project

# Scarica tutto dal bucket
gsutil -m rsync -r gs://rewts-llm-rl-data/ .

# Verifica
ls -la
```

### Metodo 2: SCP (Per file piccoli)

```bash
# Dal tuo computer locale
gcloud compute scp --recurse \
  /Users/m.zingaretti/UNI/Papers \
  rewts-training-vm:~/rewts-project \
  --zone=us-central1-a

# Questo può essere lento per file grandi
```

### Metodo 3: GitHub (Solo codice, no dati)

```bash
# Sulla VM
cd ~
git clone https://github.com/tuo-username/rewts-llm-rl.git
cd rewts-llm-rl

# Poi carica i dati separatamente con Cloud Storage
```

---

## 🎓 Esecuzione Training {#esecuzione-training}

### 1. Setup finale sulla VM

```bash
# Connetti alla VM
gcloud compute ssh rewts-training-vm --zone=us-central1-a

# Vai nella directory progetto
cd ~/rewts-project

# Attiva ambiente virtuale
source ~/venv_rewts/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Setup variabili ambiente
export GEMINI_API_KEY="your_api_key_here"

# Oppure usa .env
nano .env  # Incolla la tua API key
```

### 2. Test rapido

```bash
# Test che tutto funzioni
python scripts/verify_api_keys.py

# Test import moduli
python -c "from src.llm_agents.strategist_agent import StrategistAgent; print('OK')"
```

### 3. Avvia Training in Background

```bash
# Metodo 1: Con nohup (semplice)
nohup python scripts/train_rewts_llm_rl.py > training.log 2>&1 &

# Metodo 2: Con screen (più flessibile)
screen -S training
python scripts/train_rewts_llm_rl.py
# Premi Ctrl+A poi D per detach
# Per riattaccare: screen -r training

# Metodo 3: Con tmux (più potente)
tmux new -s training
python scripts/train_rewts_llm_rl.py
# Premi Ctrl+B poi D per detach
# Per riattaccare: tmux attach -t training
```

### 4. Monitora Training

```bash
# Visualizza log in tempo reale
tail -f training.log

# Monitora GPU
watch -n 1 nvidia-smi

# Monitora risorse
htop

# Controlla processi Python
ps aux | grep python
```

### 5. Disconnetti e Lascia Running

```bash
# Puoi disconnetterti dalla VM - il training continuerà!
exit

# Riconnetti dopo
gcloud compute ssh rewts-training-vm --zone=us-central1-a
screen -r training  # Se hai usato screen
```

---

## 💰 Gestione Costi {#gestione-costi}

### Imposta Budget Alerts

```bash
# Via console web
1. Navigation menu > Billing > Budgets & alerts
2. Create Budget
3. Nome: "ReWTS Training Budget"
4. Importo: $100
5. Alert thresholds: 50%, 90%, 100%
6. Email: tua-email@example.com
```

### Stima Costi Training

```python
# Esempio calcolo
GPU: T4
Costo: $0.35/ora (GPU) + $0.30/ora (VM) = $0.65/ora

Training duration: 4 ore
Costo training: 4h × $0.65 = $2.60

Storage (100 GB): $0.04/GB/mese = $4/mese
Egress (dati in uscita): $0.12/GB (primi 1 TB)
```

### Comandi di Controllo Costi

```bash
# Ferma VM quando non in uso
gcloud compute instances stop rewts-training-vm --zone=us-central1-a

# Riavvia quando serve
gcloud compute instances start rewts-training-vm --zone=us-central1-a

# Elimina VM (ATTENZIONE: cancella tutto!)
gcloud compute instances delete rewts-training-vm --zone=us-central1-a

# Snapshot per backup (prima di eliminare)
gcloud compute disks snapshot rewts-training-vm \
  --snapshot-names=rewts-backup-$(date +%Y%m%d) \
  --zone=us-central1-a
```

### Automazione Start/Stop

Creerò uno script per schedulare automaticamente start/stop.

---

## 🎯 Best Practices {#best-practices}

### 1. Sicurezza

```bash
# Crea Service Account per API keys invece di .env
gcloud iam service-accounts create rewts-training

# Usa Secret Manager per API keys
echo -n "your-api-key" | gcloud secrets create gemini-api-key --data-file=-
```

### 2. Backup Automatici

```bash
# Script backup automatico ogni 6 ore
crontab -e

# Aggiungi:
0 */6 * * * gsutil -m rsync -r ~/rewts-project/models/ gs://rewts-llm-rl-data/models/
0 */6 * * * gsutil -m rsync -r ~/rewts-project/data/llm_strategies/ gs://rewts-llm-rl-data/strategies/
```

### 3. Logging e Monitoring

```bash
# Setup Cloud Logging
pip install google-cloud-logging

# Nel tuo script, aggiungi:
# import google.cloud.logging
# client = google.cloud.logging.Client()
# client.setup_logging()
```

### 4. Ottimizzazione Costi

**Opzioni per risparmiare:**

1. **Preemptible VMs:** 60-91% di sconto, ma Google può interrompere
```bash
--preemptible  # Aggiungi questo flag alla creazione VM
```

2. **Sustained use discounts:** Automatici per uso prolungato

3. **Committed use discounts:** Sconto per commitment 1-3 anni

4. **Spot VMs:** Come preemptible ma più flessibili

### 5. Workflow Ottimale

```
1. Sviluppo locale → Testa su dataset piccolo
2. Colab → Prototype rapido e verifica funzionamento
3. Google Cloud → Training finale su dataset completo
4. Download risultati → Analisi locale
```

---

## 🔧 Troubleshooting {#troubleshooting}

### Quota GPU Exceeded

```
Errore: "Quota 'NVIDIA_T4_GPUS' exceeded"
```

**Soluzione:**
1. Vai su: IAM & Admin > Quotas
2. Filtra: "GPU"
3. Seleziona quota e clicca "Edit Quotas"
4. Richiedi aumento (spiega use case)
5. Approvazione in 24-48h

### Out of Memory

```bash
# Riduci batch_size nel config
# Oppure usa VM con più RAM
gcloud compute instances stop rewts-training-vm --zone=us-central1-a
# Poi ricrea con machine-type più grande
```

### Slow Data Transfer

```bash
# Usa gsutil con -m per parallelo
gsutil -m cp -r ...

# Comprimi prima di trasferire
tar -czf data.tar.gz data/
gsutil cp data.tar.gz gs://bucket/
# Sulla VM
gsutil cp gs://bucket/data.tar.gz .
tar -xzf data.tar.gz
```

### Training si interrompe

```bash
# Implementa checkpoint nel codice
# Ogni N episodi, salva stato:
# torch.save(model.state_dict(), f'checkpoint_epoch_{epoch}.pt')
```

---

## 📊 Confronto Configurazioni

### Configurazione Base (T4)
```
Machine: n1-standard-4
GPU: 1x T4
RAM: 15 GB
Storage: 100 GB SSD

Costo: ~$0.65/ora
Use case: Training standard, development
```

### Configurazione Media (V100)
```
Machine: n1-standard-8
GPU: 1x V100
RAM: 30 GB
Storage: 200 GB SSD

Costo: ~$2.50/ora
Use case: Training veloce, dataset grandi
```

### Configurazione Avanzata (A100)
```
Machine: a2-highgpu-1g
GPU: 1x A100
RAM: 85 GB
Storage: 500 GB SSD

Costo: ~$3.67/ora
Use case: Training intensivo, research
```

---

## 🎬 Quick Start

```bash
# 1. Setup progetto
gcloud projects create rewts-llm-rl
gcloud config set project rewts-llm-rl

# 2. Abilita API
gcloud services enable compute.googleapis.com storage.googleapis.com

# 3. Crea bucket
gsutil mb gs://rewts-llm-rl-data

# 4. Carica dati
gsutil -m rsync -r ~/Papers gs://rewts-llm-rl-data/

# 5. Usa script di setup (prossima sezione)
./scripts/gcp_setup.sh

# 6. Avvia training
./scripts/gcp_train.sh
```

---

## 📚 Risorse Utili

- **Console GCP:** https://console.cloud.google.com/
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **GPU Pricing:** https://cloud.google.com/compute/gpus-pricing
- **Documentation:** https://cloud.google.com/compute/docs
- **Free Tier:** https://cloud.google.com/free
- **Quotas:** https://console.cloud.google.com/iam-admin/quotas

---

## 🆘 Support

### Problemi comuni?

1. **Controlla i log:** `tail -f training.log`
2. **Verifica GPU:** `nvidia-smi`
3. **Check disk space:** `df -h`
4. **Monitor costs:** https://console.cloud.google.com/billing

### Bisogno di aiuto?

- Stack Overflow: https://stackoverflow.com/questions/tagged/google-cloud-platform
- GCP Community: https://www.googlecloudcommunity.com/
- Support: https://cloud.google.com/support
