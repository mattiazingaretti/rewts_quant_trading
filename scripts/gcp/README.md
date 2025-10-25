# GCP Deployment Scripts

Scripts per deployare ReWTSE-LLM-RL su Google Cloud Platform con **VM Spot**.

## 🚀 Quick Start

Esegui gli script in questo ordine:

```bash
# 1. Setup progetto GCP (una volta)
bash scripts/gcp/setup_project.sh

# 2. Crea Cloud Storage buckets
bash scripts/gcp/create_buckets.sh

# 3. Salva secrets (API keys)
bash scripts/gcp/setup_secrets.sh

# 4. Build e push Docker image (training)
bash scripts/gcp/build_and_push.sh

# 5. Deploy FastAPI Backtesting su VM Spot
bash scripts/gcp/deploy_fastapi_vm.sh
# Scegli opzione 2 (Spot Always-On) → $3.72/mese

# 6. (Opzionale) Setup CI/CD
bash scripts/gcp/setup_cicd.sh
```

## 📝 Script Details

### setup_project.sh
- Crea progetto GCP
- Abilita servizi necessari (Compute, Storage, Run, Functions, etc.)
- Configura region/zone defaults

### create_buckets.sh
- Crea bucket per dati e modelli
- Crea bucket per risultati
- Setup lifecycle policies (auto-move to Coldline)

### setup_secrets.sh
- Salva Gemini API key in Secret Manager
- Salva Alpaca API keys (opzionale)
- Configura IAM permissions

### create_training_vm.sh
- Crea Spot VM con GPU (T4) per training
- Installa CUDA drivers
- Clone repository
- Costo: ~$0.11/ora (Spot GPU T4)

### build_and_push.sh
- Build Docker image per training
- Push su Google Container Registry

### deploy_fastapi_vm.sh ⭐
- Deploy FastAPI server su VM Spot
- 3 opzioni disponibili:
  1. Always-On Standard: $12.40/mese (99.95% SLA)
  2. **Always-On Spot**: $3.72/mese ⭐ **CONSIGLIATA**
  3. On-Demand Spot: $0.0051/ora (start/stop manuale)
- API sempre disponibile, no cold start
- Break-even: 106 backtest/mese vs soluzioni serverless

### manage_fastapi_vm.sh
- Gestione VM FastAPI
- Comandi: start, stop, restart, status, logs, ip, delete

### setup_cicd.sh
- Setup Cloud Build trigger
- Auto-build e push Docker image su git push

## 💰 Cost Estimates

### Training (occasionale)
- Spot VM (n1-standard-4): $0.20/ora
- GPU T4 Spot: $0.11/ora
- **Total**: ~$0.31/ora
- **18 ore training completo**: ~$5.58

### Storage (mensile)
- 100 GB data: $2/mese
- 50 GB results: $0.50/mese
- **Total**: ~$2.50/mese

### Backtesting API (VM Spot) ⭐
- **Costo fisso**: $3.72/mese
- **Costo per backtest**: $0 (illimitati)
- **Break-even**: 106 backtest/mese
- **No cold start**, latenza costante

### Paper Trading (Cloud Functions)
- 720 invocazioni/mese: GRATIS
- Compute: ~$0.10/mese
- **Total**: ~$0.10/mese

### Gemini API
- 5000 calls/mese: ~$10-15
- (oppure pre-computa strategie = $0.03/mese)

### **TOTAL MONTHLY**: ~$20-25/mese

## 🔧 Configuration

### Project Settings
Edit in ogni script:
- `PROJECT_ID="rewts-quant-trading"`
- `REGION="us-central1"`
- `ZONE="us-central1-a"`

### GitHub Integration
Per CI/CD, edit `setup_cicd.sh`:
- `GITHUB_OWNER="your-username"`
- `REPO_NAME="rewts_quant_trading"`

## 📊 Monitoring

### View costs
```bash
gcloud billing accounts list
gcloud billing projects describe rewts-quant-trading
```

### View running VMs
```bash
gcloud compute instances list
```

### View FastAPI VM status
```bash
bash scripts/gcp/manage_fastapi_vm.sh status
```

### View FastAPI logs
```bash
bash scripts/gcp/manage_fastapi_vm.sh logs
```

### Get FastAPI API URL
```bash
bash scripts/gcp/manage_fastapi_vm.sh ip
```

### View storage usage
```bash
gsutil du -sh gs://rewts-trading-data
gsutil du -sh gs://rewts-trading-results
```

## 🛑 Stop/Delete Resources

### Stop training VM (to save costs)
```bash
gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

### Delete training VM
```bash
gcloud compute instances delete rewts-training-spot --zone=us-central1-a
```

### Manage FastAPI VM
```bash
# Stop (save costs)
bash scripts/gcp/manage_fastapi_vm.sh stop

# Start again
bash scripts/gcp/manage_fastapi_vm.sh start

# Delete completely
bash scripts/gcp/manage_fastapi_vm.sh delete
```

### Delete entire project (caution!)
```bash
gcloud projects delete rewts-quant-trading
```

## 🔐 Security Best Practices

1. **Never commit secrets** to git
2. Use **Secret Manager** for API keys
3. Use **IAM roles** for service accounts
4. Enable **budget alerts** (important!)
5. Use **VPC firewall rules** for training VMs
6. **Restrict firewall** for FastAPI (only your IPs if needed)

## 📚 Resources

- GCP Pricing: https://cloud.google.com/pricing/calculator
- Spot VMs: https://cloud.google.com/compute/docs/instances/spot
- Secret Manager: https://cloud.google.com/secret-manager/docs

## ❓ Troubleshooting

### "Quota exceeded" error
- Request quota increase in GCP Console
- Common: GPU quota in region

### Spot VM preempted frequently
- Try different zone: `gcloud compute zones list`
- VM FastAPI has systemd auto-restart (downtime <1 min)

### Cloud Build fails
- Check IAM permissions
- Verify Docker images build locally first

### FastAPI VM not responding
- Check VM status: `bash scripts/gcp/manage_fastapi_vm.sh status`
- View logs: `bash scripts/gcp/manage_fastapi_vm.sh logs`
- Restart: `bash scripts/gcp/manage_fastapi_vm.sh restart`

### High costs
- Check budget alerts
- Stop unused VMs (training VM dopo uso!)
- Use lifecycle policies for storage
- Pre-compute LLM strategies

## 🎯 Typical Workflow

### 1. Setup iniziale (una volta)
```bash
bash scripts/gcp/setup_project.sh
bash scripts/gcp/create_buckets.sh
bash scripts/gcp/setup_secrets.sh
bash scripts/gcp/build_and_push.sh
bash scripts/gcp/deploy_fastapi_vm.sh  # Opzione 2
```

### 2. Training (quando serve)
```bash
# Create training VM
bash scripts/gcp/create_training_vm.sh

# SSH and train
gcloud compute ssh rewts-training-spot --zone=us-central1-a
cd /home/jupyter/rewts_quant_trading
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)
python scripts/train_rewts_llm_rl.py

# Stop VM quando finito (IMPORTANTE!)
gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

### 3. Backtesting (sempre disponibile)
```python
from examples.backtesting_client_example import BacktestingClient

# Get VM IP
vm_ip = "35.123.45.67"  # bash scripts/gcp/manage_fastapi_vm.sh ip

client = BacktestingClient(vm_ip=vm_ip)
result = client.run_backtest(
    ticker="AAPL",
    start_date="2020-01-01",
    end_date="2020-12-31"
)
```

### 4. Paper Trading (automatico)
```bash
# Deploy paper trading function (opzionale)
bash scripts/gcp/deploy_paper_trader.sh
```

## 💡 Cost Optimization Tips

1. **Training VM**: SEMPRE stop dopo uso → risparmio 100% quando non serve
2. **FastAPI VM**: Spot Always-On → 70% sconto vs Standard
3. **Storage**: Lifecycle policies → auto-move a Coldline dopo 90 giorni
4. **Gemini API**: Pre-computa strategie → 95% risparmio
5. **Budget alerts**: Setup a $50/mese per sicurezza

## 🎉 Summary

- **Setup**: 15 minuti
- **Training**: ~$5.58 per run (18h)
- **Backtesting**: $3.72/mese fisso, illimitati backtest
- **Total**: ~$20-25/mese uso regolare

Ottimo rapporto qualità/prezzo per sistema trading quantitativo! 🚀
