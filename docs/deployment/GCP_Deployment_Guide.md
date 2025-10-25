# Guida Deployment su Google Cloud Platform (GCP)
## ReWTSE-LLM-RL - Ottimizzazione Costi

Questa guida ti mostra come deployare il sistema ReWTSE-LLM-RL su Google Cloud Platform ottimizzando al massimo i costi.

---

## 📊 Stima Costi Mensili

### Scenario 1: Uso Minimo (Solo Testing)
- **Training**: 1 volta/mese con Spot GPU → **$10-15**
- **Storage**: 50 GB → **$1**
- **Gemini API**: 1000 calls → **$0-5**
- **Totale**: **~$15-20/mese**

### Scenario 2: Uso Regolare (Ricerca Attiva)
- **Training**: 4 volte/mese con Spot GPU → **$40-60**
- **Backtesting**: Cloud Run → **$5-10**
- **Storage**: 100 GB → **$2**
- **Gemini API**: 5000 calls → **$10-20**
- **Totale**: **~$60-90/mese**

### Scenario 3: Uso Intensivo (Production-like)
- **Training**: Settimanale con Spot GPU → **$100-150**
- **Paper Trading**: Cloud Run 24/7 → **$20-30**
- **Storage**: 200 GB + Cloud SQL → **$15**
- **Gemini API**: 20000 calls → **$40-60**
- **Monitoring**: Cloud Monitoring → **$5**
- **Totale**: **~$180-250/mese**

**Confronto con hardware locale**: RTX 3060 costa ~€350 one-time, si ripaga in 4-6 mesi se usi GCP intensivamente.

---

## 🏗️ Architettura Deployment

```
┌─────────────────────────────────────────────────────┐
│              Google Cloud Platform                  │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  1. Training (Compute Engine GPU - SPOT)    │   │
│  │     - Avviato on-demand                      │   │
│  │     - GPU: T4 / L4 / V100                    │   │
│  │     - VRAM: 16-24 GB                         │   │
│  │     - Salva modelli → Cloud Storage          │   │
│  └──────────────┬──────────────────────────────┘   │
│                 │                                    │
│  ┌──────────────▼──────────────────────────────┐   │
│  │  2. Cloud Storage (Standard)                │   │
│  │     - Dati raw (Yahoo Finance)               │   │
│  │     - Modelli addestrati (.pt)               │   │
│  │     - Strategie LLM pre-computate (.json)    │   │
│  │     - Risultati backtesting                  │   │
│  └──────────────┬──────────────────────────────┘   │
│                 │                                    │
│  ┌──────────────▼──────────────────────────────┐   │
│  │  3. Backtesting (Cloud Run)                 │   │
│  │     - Serverless, pay-per-use                │   │
│  │     - Auto-scaling 0 → N                     │   │
│  │     - CPU-only (no GPU needed)               │   │
│  └──────────────┬──────────────────────────────┘   │
│                 │                                    │
│  ┌──────────────▼──────────────────────────────┐   │
│  │  4. Paper Trading (Cloud Functions)         │   │
│  │     - Esegue ogni ora (Cloud Scheduler)      │   │
│  │     - Chiama Alpaca API                      │   │
│  │     - Legge strategie da Storage             │   │
│  └──────────────┬──────────────────────────────┘   │
│                 │                                    │
│  ┌──────────────▼──────────────────────────────┐   │
│  │  5. Gemini API (Vertex AI)                  │   │
│  │     - Strategist Agent                       │   │
│  │     - Analyst Agent                          │   │
│  │     - Nativo su GCP (bassa latenza)          │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  6. Monitoring & Logging                     │   │
│  │     - Cloud Logging: Logs centralizzati      │   │
│  │     - Cloud Monitoring: Metriche performance │   │
│  │     - Budget Alerts: Avvisi costi            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Strategia Ottimizzazione Costi

### 1. Training: Usa Spot VMs (60-91% di sconto)

**Spot VMs** sono istanze preemptible che costano 1/3 - 1/10 del prezzo normale ma possono essere terminate da Google.

**Perché funziona per noi**:
- Training può essere interrotto e ripreso (checkpointing)
- Non serve disponibilità 24/7
- Risparmio enorme

**Prezzi GPU Spot** (us-central1):

| GPU | VRAM | Prezzo Normal | Prezzo Spot | Risparmio |
|-----|------|---------------|-------------|-----------|
| T4 | 16 GB | $0.35/ora | **$0.11/ora** | 69% |
| L4 | 24 GB | $0.70/ora | **$0.22/ora** | 69% |
| V100 | 16 GB | $2.48/ora | **$0.74/ora** | 70% |
| A100 (40GB) | 40 GB | $3.67/ora | **$1.10/ora** | 70% |

**Training completo (6 ticker, 12-18 ore)**:
- **T4 Spot**: $0.11/ora × 18h = **~$2-3** per run 🎯
- **L4 Spot**: $0.22/ora × 12h = **~$3-4** per run

### 2. Storage: Cloud Storage Standard

**Prezzi** (us-central1):
- **Standard Storage**: $0.020/GB/mese
- **Nearline** (accesso <1 volta/mese): $0.010/GB/mese
- **Coldline** (accesso <1 volta/trimestre): $0.004/GB/mese

**Strategia**:
- Dati raw e modelli recenti: **Standard** (~50 GB = $1/mese)
- Modelli vecchi (archivio): **Nearline** (100 GB = $1/mese)
- Backup storici: **Coldline** (200 GB = $0.80/mese)

### 3. Backtesting: Cloud Run Serverless

**Prezzi**:
- CPU: $0.00002400/vCPU-second
- Memory: $0.00000250/GB-second
- Requests: Prime 2M free, poi $0.40/milione

**Esempio** (backtesting 10 minuti):
- 2 vCPU × 600s = 1200 vCPU-seconds = **$0.03**
- 4 GB × 600s = 2400 GB-seconds = **$0.006**
- **Totale**: ~$0.04 per backtesting run

**Vantaggio**: Scali a 0 quando non usi = $0

### 4. Paper Trading: Cloud Functions

**Prezzi**:
- Prime 2M invocazioni/mese: **GRATIS**
- Poi $0.40/milione
- Compute: $0.0000025/GB-second

**Esempio** (esecuzione ogni ora, 24/7):
- 24 × 30 = 720 invocazioni/mese = **GRATIS**
- Compute: trascurabile (~$0.10/mese)

### 5. Gemini API

**Prezzi Gemini 2.0 Flash**:
- Input: $0.075 per 1M tokens (~$0.0001 per 1K tokens)
- Output: $0.30 per 1M tokens (~$0.0003 per 1K tokens)

**Stima per Strategist prompt** (6 ticker):
- Input: ~5K tokens/ticker = 30K tokens = **$0.003**
- Output: ~1K tokens/ticker = 6K tokens = **$0.002**
- **Totale per strategia mensile**: ~$0.005 × 6 = **$0.03**

**Strategia risparmio**:
1. **Pre-computa strategie** durante training e salvale → 1 call/mese invece di 1 call/giorno
2. **Cache responses** per lo stesso periodo temporale
3. Usa batch requests per più ticker insieme

---

## 🚀 Setup Iniziale GCP

### 1. Prerequisiti

```bash
# Installa Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login e setup progetto
gcloud auth login
gcloud projects create rewts-quant-trading --name="ReWTSE Trading"
gcloud config set project rewts-quant-trading

# Abilita servizi necessari
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

### 2. Setup Budget Alerts (Importante!)

```bash
# Crea budget alert per non spendere troppo
gcloud billing budgets create \
  --billing-account=YOUR-BILLING-ACCOUNT-ID \
  --display-name="ReWTS Trading Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### 3. Crea Cloud Storage Bucket

```bash
# Bucket per dati e modelli (us-central1 = più economico)
gsutil mb -c STANDARD -l us-central1 gs://rewts-trading-data

# Bucket per risultati (nearline, più economico)
gsutil mb -c NEARLINE -l us-central1 gs://rewts-trading-results

# Lifecycle policy (sposta vecchi dati a Coldline dopo 90 giorni)
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://rewts-trading-data
```

---

## 🐳 Dockerizzazione

### Dockerfile per Training

```dockerfile
# Usa immagine base con PyTorch e CUDA
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Installa dipendenze sistema
RUN apt-get update && apt-get install -y \\
    git \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Installa dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY . .

# Environment variables (override con --env)
ENV GEMINI_API_KEY=""
ENV GCS_BUCKET="rewts-trading-data"

# Entrypoint
ENTRYPOINT ["python", "scripts/train_rewts_llm_rl.py"]
```

### Dockerfile per Backtesting (Cloud Run)

```dockerfile
# Immagine più leggera per backtesting (no GPU)
FROM python:3.10-slim

WORKDIR /app

# Installa solo dipendenze necessarie per backtesting
COPY requirements-inference.txt .
RUN pip install --no-cache-dir -r requirements-inference.txt

COPY . .

# Expose port per Cloud Run
EXPOSE 8080

# Comando per avviare API
CMD ["python", "api/backtesting_server.py"]
```

### Build e Push su Google Container Registry

```bash
# Setup Docker auth per GCP
gcloud auth configure-docker

# Build immagine training
docker build -f docker/Dockerfile.training -t gcr.io/rewts-quant-trading/training:latest .

# Build immagine backtesting
docker build -f docker/Dockerfile.backtesting -t gcr.io/rewts-quant-trading/backtesting:latest .

# Push su GCR
docker push gcr.io/rewts-quant-trading/training:latest
docker push gcr.io/rewts-quant-trading/backtesting:latest
```

---

## 🎓 Training su Compute Engine Spot

### Script per Creare VM Spot con GPU

```bash
#!/bin/bash
# scripts/gcp/create_training_vm.sh

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"  # Zone con GPU disponibili
INSTANCE_NAME="rewts-training-spot"
MACHINE_TYPE="n1-standard-4"  # 4 vCPU, 15 GB RAM
GPU_TYPE="nvidia-tesla-t4"
GPU_COUNT=1

gcloud compute instances create $INSTANCE_NAME \\
  --project=$PROJECT_ID \\
  --zone=$ZONE \\
  --machine-type=$MACHINE_TYPE \\
  --accelerator=type=$GPU_TYPE,count=$GPU_COUNT \\
  --provisioning-model=SPOT \\
  --instance-termination-action=STOP \\
  --maintenance-policy=TERMINATE \\
  --image-family=pytorch-latest-gpu \\
  --image-project=deeplearning-platform-release \\
  --boot-disk-size=100GB \\
  --boot-disk-type=pd-standard \\
  --scopes=https://www.googleapis.com/auth/cloud-platform \\
  --metadata=startup-script='#!/bin/bash
    # Install CUDA drivers
    /opt/deeplearning/install-driver.sh

    # Clone repo
    cd /home
    git clone https://github.com/YOUR-USERNAME/rewts_quant_trading.git
    cd rewts_quant_trading

    # Setup environment
    pip install -r requirements.txt

    # Set environment variables
    export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="gemini-api-key")

    # Download data from GCS
    gsutil -m cp -r gs://rewts-trading-data/raw ./data/

    echo "VM ready for training! SSH and run: python scripts/train_rewts_llm_rl.py"
  '

echo "VM $INSTANCE_NAME created! Training will cost ~$0.11/hour with T4 Spot"
echo ""
echo "SSH into VM:"
echo "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "Start training:"
echo "  python scripts/train_rewts_llm_rl.py"
echo ""
echo "Monitor GPU usage:"
echo "  watch -n 1 nvidia-smi"
```

### Script Training Automatico con Checkpointing

```python
# scripts/train_with_checkpoint.py
"""
Training script ottimizzato per Spot VMs con auto-checkpoint
"""
import os
import time
import torch
from google.cloud import storage

def check_preemption():
    """Check se la VM sta per essere preempted"""
    try:
        import requests
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/preempted",
            headers={"Metadata-Flavor": "Google"},
            timeout=1
        )
        return response.text == "TRUE"
    except:
        return False

def save_checkpoint_to_gcs(checkpoint_path, bucket_name="rewts-trading-data"):
    """Salva checkpoint su Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"checkpoints/{os.path.basename(checkpoint_path)}")
    blob.upload_from_filename(checkpoint_path)
    print(f"✅ Checkpoint salvato su GCS: gs://{bucket_name}/checkpoints/")

def load_checkpoint_from_gcs(checkpoint_name, bucket_name="rewts-trading-data"):
    """Carica checkpoint da Cloud Storage"""
    local_path = f"/tmp/{checkpoint_name}"
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"checkpoints/{checkpoint_name}")

    if blob.exists():
        blob.download_to_filename(local_path)
        print(f"✅ Checkpoint caricato da GCS")
        return torch.load(local_path)
    return None

def train_with_preemption_handling():
    """Main training loop con gestione preemption"""

    # Carica checkpoint esistente se presente
    checkpoint = load_checkpoint_from_gcs("latest_checkpoint.pt")

    start_chunk = 0
    start_episode = 0

    if checkpoint:
        start_chunk = checkpoint['chunk_idx']
        start_episode = checkpoint['episode']
        print(f"🔄 Riprendendo da chunk {start_chunk}, episode {start_episode}")

    # Training loop
    for chunk_idx in range(start_chunk, num_chunks):
        for episode in range(start_episode if chunk_idx == start_chunk else 0, episodes_per_chunk):

            # Training step...
            # ... (tuo codice di training)

            # Ogni 10 episodi, salva checkpoint
            if episode % 10 == 0:
                checkpoint_data = {
                    'chunk_idx': chunk_idx,
                    'episode': episode,
                    'model_state': agent.state_dict(),
                    'optimizer_state': optimizer.state_dict(),
                    'metrics': metrics
                }
                torch.save(checkpoint_data, '/tmp/latest_checkpoint.pt')
                save_checkpoint_to_gcs('/tmp/latest_checkpoint.pt')

            # Check preemption ogni 100 step
            if episode % 100 == 0 and check_preemption():
                print("⚠️  Preemption rilevata! Salvando checkpoint finale...")
                checkpoint_data = {
                    'chunk_idx': chunk_idx,
                    'episode': episode,
                    'model_state': agent.state_dict(),
                    'optimizer_state': optimizer.state_dict(),
                    'metrics': metrics
                }
                torch.save(checkpoint_data, '/tmp/preemption_checkpoint.pt')
                save_checkpoint_to_gcs('/tmp/preemption_checkpoint.pt')
                print("✅ Checkpoint salvato! La VM può essere fermata ora.")
                return

        # Reset start_episode per next chunk
        start_episode = 0

    print("🎉 Training completato!")

if __name__ == "__main__":
    train_with_preemption_handling()
```

### Costo Training Totale

**Setup consigliato** (T4 Spot, 18 ore per 6 ticker):
```
Compute Engine Spot (n1-standard-4): $0.0200/ora × 18h = $0.36
GPU T4 Spot: $0.11/ora × 18h = $1.98
Storage SSD 100GB: $0.17/mese (prorate)
Egress data: ~$0.10
──────────────────────────────────────────────
TOTALE per training run: ~$2.50 🎯
```

**Confronto**:
- Hardware locale (RTX 3060): ~€350 one-time
- GCP training mensile (4 run): ~$10/mese
- **Break-even**: 35 mesi (~3 anni)

**Quando conviene GCP**:
- Training occasionale (<1 volta/settimana)
- Non vuoi investire in GPU
- Vuoi flessibilità di GPU diverse

**Quando conviene hardware locale**:
- Training frequente (>1 volta/giorno)
- Uso GPU per altri progetti
- Training >3 anni

---

## 🔄 Backtesting su Cloud Run

### API Server per Backtesting

```python
# api/backtesting_server.py
"""
Cloud Run API per backtesting
"""
from flask import Flask, request, jsonify
from google.cloud import storage
import torch
import pandas as pd

app = Flask(__name__)

# Carica modelli all'avvio
@app.before_first_request
def load_models():
    global ensemble_controller

    # Download modelli da GCS
    client = storage.Client()
    bucket = client.bucket("rewts-trading-data")

    # Download ensemble models
    for i in range(NUM_CHUNKS):
        blob = bucket.blob(f"models/ddqn_chunk_{i}.pt")
        blob.download_to_filename(f"/tmp/ddqn_chunk_{i}.pt")

    # Load ensemble
    ensemble_controller = load_ensemble_from_dir("/tmp")
    print("✅ Modelli caricati")

@app.route('/backtest', methods=['POST'])
def backtest():
    """
    Endpoint per backtesting

    Body:
    {
        "ticker": "AAPL",
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "strategy": "llm_generated"
    }
    """
    data = request.json
    ticker = data.get('ticker')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Esegui backtesting
    results = run_backtest(
        ensemble_controller,
        ticker,
        start_date,
        end_date
    )

    return jsonify({
        'ticker': ticker,
        'sharpe_ratio': results['sharpe'],
        'max_drawdown': results['max_drawdown'],
        'cumulative_return': results['cum_return'],
        'trades': results['trades']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Deploy su Cloud Run

```bash
#!/bin/bash
# scripts/gcp/deploy_backtesting.sh

# Build e push immagine
docker build -f docker/Dockerfile.backtesting -t gcr.io/rewts-quant-trading/backtesting:latest .
docker push gcr.io/rewts-quant-trading/backtesting:latest

# Deploy su Cloud Run
gcloud run deploy backtesting-api \\
  --image gcr.io/rewts-quant-trading/backtesting:latest \\
  --platform managed \\
  --region us-central1 \\
  --memory 4Gi \\
  --cpu 2 \\
  --timeout 600 \\
  --concurrency 10 \\
  --min-instances 0 \\
  --max-instances 5 \\
  --set-env-vars GCS_BUCKET=rewts-trading-data \\
  --allow-unauthenticated

echo "✅ API deployed!"
echo "Test with:"
echo 'curl -X POST https://backtesting-api-xxx.run.app/backtest \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '"'"'{"ticker": "AAPL", "start_date": "2020-01-01", "end_date": "2020-12-31"}'"'"
```

**Costi Cloud Run**:
- **Scale to zero**: $0 quando non usi
- **Per request**: ~$0.04 per backtesting di 10 minuti
- **Mensile** (10 backtest/giorno): ~$12/mese

---

## ⏰ Paper Trading con Cloud Functions + Scheduler

### Cloud Function per Paper Trading

```python
# functions/paper_trader/main.py
"""
Cloud Function per paper trading automatico
"""
import os
from google.cloud import storage
from alpaca.trading.client import TradingClient
import json

def paper_trade(request):
    """
    Eseguito ogni ora da Cloud Scheduler
    """
    # Load API keys da Secret Manager
    alpaca_key = os.environ.get('ALPACA_API_KEY')
    alpaca_secret = os.environ.get('ALPACA_SECRET_KEY')

    # Init Alpaca client
    trading_client = TradingClient(alpaca_key, alpaca_secret, paper=True)

    # Load strategie da GCS
    client = storage.Client()
    bucket = client.bucket("rewts-trading-data")
    blob = bucket.blob("strategies/current_month_strategies.json")
    strategies = json.loads(blob.download_as_text())

    # Esegui trades
    for ticker, strategy in strategies.items():
        current_position = get_position(trading_client, ticker)

        if strategy == "LONG" and current_position <= 0:
            # Buy signal
            place_order(trading_client, ticker, "buy", quantity=10)
            print(f"📈 BUY {ticker}")

        elif strategy == "SHORT" and current_position >= 0:
            # Sell signal
            place_order(trading_client, ticker, "sell", quantity=10)
            print(f"📉 SELL {ticker}")

    return {'status': 'success', 'trades_executed': len(strategies)}
```

### Deploy Cloud Function

```bash
#!/bin/bash
# scripts/gcp/deploy_paper_trader.sh

# Deploy function
gcloud functions deploy paper-trader \\
  --runtime python310 \\
  --trigger-http \\
  --entry-point paper_trade \\
  --region us-central1 \\
  --memory 256MB \\
  --timeout 60s \\
  --set-env-vars GCS_BUCKET=rewts-trading-data \\
  --set-secrets ALPACA_API_KEY=alpaca-api-key:latest,ALPACA_SECRET_KEY=alpaca-secret-key:latest

# Crea scheduler per eseguire ogni ora
gcloud scheduler jobs create http paper-trading-hourly \\
  --schedule="0 * * * *" \\
  --uri="https://us-central1-rewts-quant-trading.cloudfunctions.net/paper-trader" \\
  --http-method=POST \\
  --location=us-central1

echo "✅ Paper trading function deployed e scheduled ogni ora!"
```

**Costi Cloud Functions + Scheduler**:
- **Invocazioni**: 720/mese (ogni ora) = GRATIS (sotto 2M)
- **Compute**: ~$0.10/mese
- **Scheduler**: $0.10/job/mese
- **Totale**: ~**$0.20/mese** 🎯

---

## 📊 Monitoring e Cost Control

### Setup Cloud Monitoring Dashboard

```bash
# scripts/gcp/setup_monitoring.sh

# Crea dashboard per monitoring
gcloud monitoring dashboards create --config-from-file=- <<EOF
{
  "displayName": "ReWTS Trading Dashboard",
  "dashboardFilters": [],
  "gridLayout": {
    "widgets": [
      {
        "title": "Training VM CPU Usage",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"gce_instance\" AND metric.type=\"compute.googleapis.com/instance/cpu/utilization\""
              }
            }
          }]
        }
      },
      {
        "title": "Cloud Run Requests",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
              }
            }
          }]
        }
      },
      {
        "title": "Storage Usage",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"gcs_bucket\" AND metric.type=\"storage.googleapis.com/storage/total_bytes\""
              }
            }
          }]
        }
      }
    ]
  }
}
EOF
```

### Cost Alerts

```python
# scripts/gcp/setup_cost_alerts.py
"""
Setup budget alerts per evitare sorprese
"""
from google.cloud import billing_budgets_v1

def create_budget_alert(project_id, billing_account, budget_amount=100):
    client = billing_budgets_v1.BudgetServiceClient()

    budget = billing_budgets_v1.Budget()
    budget.display_name = "ReWTS Monthly Budget"
    budget.budget_filter.projects = [f"projects/{project_id}"]

    # Set budget amount
    budget.amount.specified_amount.currency_code = "USD"
    budget.amount.specified_amount.units = budget_amount

    # Alert thresholds
    budget.threshold_rules = [
        billing_budgets_v1.ThresholdRule(threshold_percent=0.5),  # 50%
        billing_budgets_v1.ThresholdRule(threshold_percent=0.9),  # 90%
        billing_budgets_v1.ThresholdRule(threshold_percent=1.0),  # 100%
    ]

    # Create budget
    parent = f"billingAccounts/{billing_account}"
    response = client.create_budget(parent=parent, budget=budget)
    print(f"✅ Budget alert creato: {response.name}")

if __name__ == "__main__":
    create_budget_alert(
        project_id="rewts-quant-trading",
        billing_account="YOUR-BILLING-ACCOUNT-ID",
        budget_amount=100  # $100/mese
    )
```

---

## 🤖 CI/CD con Cloud Build

### cloudbuild.yaml

```yaml
# cloudbuild.yaml
steps:
  # Build training image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-f', 'docker/Dockerfile.training',
      '-t', 'gcr.io/$PROJECT_ID/training:$SHORT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/training:latest',
      '.'
    ]

  # Build backtesting image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-f', 'docker/Dockerfile.backtesting',
      '-t', 'gcr.io/$PROJECT_ID/backtesting:$SHORT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/backtesting:latest',
      '.'
    ]

  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/training:$SHORT_SHA']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/training:latest']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/backtesting:$SHORT_SHA']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/backtesting:latest']

  # Deploy backtesting to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: [
      'run', 'deploy', 'backtesting-api',
      '--image', 'gcr.io/$PROJECT_ID/backtesting:$SHORT_SHA',
      '--region', 'us-central1',
      '--platform', 'managed',
      '--allow-unauthenticated'
    ]

# Store images for 30 days
images:
  - 'gcr.io/$PROJECT_ID/training:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/training:latest'
  - 'gcr.io/$PROJECT_ID/backtesting:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/backtesting:latest'

# Timeout
timeout: 1800s  # 30 minuti
```

### Setup Cloud Build Trigger

```bash
# Connect GitHub repo
gcloud builds triggers create github \\
  --repo-name=rewts_quant_trading \\
  --repo-owner=YOUR-GITHUB-USERNAME \\
  --branch-pattern="^main$" \\
  --build-config=cloudbuild.yaml \\
  --description="Build and deploy on main branch push"
```

---

## 📋 Checklist Setup Completo

### 1. Setup Iniziale (una volta)
- [ ] Crea progetto GCP
- [ ] Abilita billing e setup budget alerts
- [ ] Abilita servizi (Compute, Storage, Run, Functions, etc.)
- [ ] Crea Storage buckets
- [ ] Setup lifecycle policies per storage
- [ ] Salva secrets (Gemini API key, Alpaca keys) in Secret Manager

### 2. Development
- [ ] Crea Dockerfile per training
- [ ] Crea Dockerfile per backtesting
- [ ] Build e push immagini su GCR
- [ ] Setup CI/CD con Cloud Build

### 3. Training
- [ ] Upload dati raw su Cloud Storage
- [ ] Crea VM Spot con GPU
- [ ] Esegui training con checkpointing
- [ ] Salva modelli su Cloud Storage
- [ ] Termina VM Spot

### 4. Backtesting
- [ ] Deploy API su Cloud Run
- [ ] Test API endpoint
- [ ] Setup monitoring

### 5. Paper Trading
- [ ] Deploy Cloud Function
- [ ] Setup Cloud Scheduler
- [ ] Test execution manuale
- [ ] Verifica trades su Alpaca

### 6. Monitoring
- [ ] Setup Cloud Monitoring dashboard
- [ ] Configure log-based metrics
- [ ] Test budget alerts

---

## 💰 Riepilogo Costi Ottimizzati

### Monthly Costs Breakdown (Uso Regolare)

| Componente | Dettagli | Costo/Mese |
|------------|----------|------------|
| **Training** | T4 Spot × 4 training/mese (72h tot) | $8-12 |
| **Storage Standard** | 100 GB modelli + dati | $2 |
| **Storage Nearline** | 200 GB archivio | $2 |
| **Cloud Run** | Backtesting 20 run/mese | $1 |
| **Cloud Functions** | Paper trading 720 invocazioni | $0.20 |
| **Cloud Scheduler** | 1 job | $0.10 |
| **Gemini API** | 5000 calls strategist/analyst | $10-15 |
| **Networking** | Egress data ~50 GB | $5 |
| **Cloud Monitoring** | Logs e metrics | $2 |
| **TOTALE** | | **~$30-40/mese** 🎯 |

### Confronto Alternative

| Soluzione | Setup Cost | Monthly Cost | Break-even |
|-----------|------------|--------------|------------|
| **GCP Ottimizzato** | $0 | $30-40 | N/A |
| **Hardware Locale** (RTX 3060) | €350 | €5 (elettricità) | 12-14 mesi |
| **GCP Non-ottimizzato** (no Spot) | $0 | $150-200 | N/A |
| **AWS** (simile) | $0 | $40-60 | N/A |
| **Colab Pro+** | $0 | $50 | N/A |

---

## 🎯 Best Practices Risparmio

### 1. Usa Spot VMs per Training
💰 **Risparmio**: 60-91%
- Implementa checkpointing robusto
- Usa `--provisioning-model=SPOT`

### 2. Scale to Zero con Cloud Run
💰 **Risparmio**: 100% quando non usi
- Usa Cloud Run invece di VM sempre accese
- Min instances = 0

### 3. Lifecycle Policies per Storage
💰 **Risparmio**: 50-80% su dati vecchi
- Standard → Nearline (30 giorni)
- Nearline → Coldline (90 giorni)

### 4. Pre-computa Strategie LLM
💰 **Risparmio**: 95% su Gemini API
- Genera 1 volta/mese invece di real-time
- Cache risultati

### 5. Usa Regioni Economiche
💰 **Risparmio**: 10-30%
- `us-central1` (Iowa) = più economico
- Evita `europe-west2` (London) = costoso

### 6. Budget Alerts
💰 **Risparmio**: previeni overspending
- Alert a 50%, 90%, 100%
- Email + SMS

### 7. Delete Unused Resources
💰 **Risparmio**: vario
- Snapshot vecchi
- VM fermate ma non terminate
- Load balancers inutilizzati

---

## 📞 Support e Troubleshooting

### Problema: Spot VM viene preemptata troppo spesso

**Soluzione**:
1. Scegli zone diverse con meno demand:
```bash
# Check disponibilità GPU per zona
gcloud compute accelerator-types list --filter="zone:us-central1-*"
```

2. Usa committed use discounts (se training regolare):
```bash
gcloud compute commitments create --accelerator-type=nvidia-tesla-t4 --accelerator-count=1
```

### Problema: Cloud Run timeout (>600s)

**Soluzione**: Dividi backtesting in chunk più piccoli o usa Compute Engine.

### Problema: Costi Gemini API alti

**Soluzione**:
1. Pre-computa strategie mensili
2. Cache responses con Cloud Memorystore
3. Usa batch requests

---

## 🚀 Getting Started Rapido

```bash
# 1. Clone repo
git clone https://github.com/YOUR-USERNAME/rewts_quant_trading.git
cd rewts_quant_trading

# 2. Setup GCP (esegui scripts in order)
bash scripts/gcp/setup_project.sh
bash scripts/gcp/create_buckets.sh
bash scripts/gcp/setup_secrets.sh

# 3. Build e deploy
bash scripts/gcp/build_and_push.sh

# 4. Esegui primo training
bash scripts/gcp/create_training_vm.sh
gcloud compute ssh rewts-training-spot --zone=us-central1-a
# Nella VM:
python scripts/train_rewts_llm_rl.py

# 5. Deploy backtesting API
bash scripts/gcp/deploy_backtesting.sh

# 6. Deploy paper trader
bash scripts/gcp/deploy_paper_trader.sh

# 7. Monitor costs
gcloud billing budgets list
```

---

## 📚 Risorse Aggiuntive

- **GCP Pricing Calculator**: https://cloud.google.com/products/calculator
- **Spot VM Best Practices**: https://cloud.google.com/compute/docs/instances/preemptible
- **Cloud Run Pricing**: https://cloud.google.com/run/pricing
- **Gemini API Pricing**: https://ai.google.dev/pricing

---

**Nota Finale**: Questa architettura è ottimizzata per costi minimi mantenendo performance elevate. Con ~$30-40/mese puoi operare un sistema di trading quantitativo sofisticato su GCP. 🎉
