# Deployment GCP con VM Spot - Guida Rapida
## ReWTSE-LLM-RL Trading System

Deployment ottimizzato per costi usando **VM Spot con FastAPI**.

---

## 💰 Costi Mensili

| Componente | Costo |
|------------|-------|
| Training (4 run/mese, 18h cad) | $22 |
| Backtesting VM Spot Always-On | **$3.72** |
| Storage (150 GB) | $3 |
| Gemini API (5000 calls) | $15 |
| **TOTALE** | **~$44/mese** |

---

## 🚀 Setup Completo (15 minuti)

### 1. Setup GCP Project

```bash
cd rewts_quant_trading

# Setup progetto
bash scripts/gcp/setup_project.sh

# Crea buckets
bash scripts/gcp/create_buckets.sh

# Salva secrets (Gemini API key)
bash scripts/gcp/setup_secrets.sh
```

### 2. Deploy Backtesting API (VM Spot)

```bash
# Deploy FastAPI su VM Spot
bash scripts/gcp/deploy_fastapi_vm.sh

# Quando richiesto, scegli: 2 (Spot Always-On)
# Costo: $3.72/mese fisso
```

Dopo il deploy, ottieni:
- IP pubblico della VM
- API FastAPI su porta 8000
- Auto-restart systemd service
- Firewall rule configurata

### 3. Test API

```bash
# Get VM IP
bash scripts/gcp/manage_fastapi_vm.sh ip

# Test health
curl http://YOUR_VM_IP:8000/health

# Test backtest
curl -X POST http://YOUR_VM_IP:8000/backtest \
  -H 'Content-Type: application/json' \
  -d '{"ticker": "AAPL", "start_date": "2020-01-01", "end_date": "2020-12-31"}'
```

### 4. Usa da Python

```python
from examples.backtesting_client_example import BacktestingClient

# Initialize client
client = BacktestingClient(vm_ip="YOUR_VM_IP")

# Run backtest
result = client.run_backtest(
    ticker="AAPL",
    start_date="2020-01-01",
    end_date="2020-12-31"
)

print(f"Sharpe: {result['sharpe_ratio']:.3f}")
print(f"Return: {result['cumulative_return']:.2%}")
```

---

## 🎓 Training (quando serve)

### Crea Training VM con GPU

```bash
# Crea Spot VM con GPU T4
bash scripts/gcp/create_training_vm.sh

# Costo: ~$0.31/ora ($5.58 per 18h training)
```

### SSH e Training

```bash
# SSH nella VM
gcloud compute ssh rewts-training-spot --zone=us-central1-a

# Nella VM:
cd /home/jupyter/rewts_quant_trading
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)

# Start training
python scripts/train_rewts_llm_rl.py

# Monitor GPU
watch -n 1 nvidia-smi
```

### Stop VM (IMPORTANTE!)

```bash
# Quando training finito, STOP la VM per non pagare
gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

---

## 🔧 Gestione VM Backtesting

### Comandi Utili

```bash
# Get IP
bash scripts/gcp/manage_fastapi_vm.sh ip

# Check status
bash scripts/gcp/manage_fastapi_vm.sh status

# View logs
bash scripts/gcp/manage_fastapi_vm.sh logs

# Restart
bash scripts/gcp/manage_fastapi_vm.sh restart

# Stop (save costs)
bash scripts/gcp/manage_fastapi_vm.sh stop

# Start again
bash scripts/gcp/manage_fastapi_vm.sh start

# Delete
bash scripts/gcp/manage_fastapi_vm.sh delete
```

### Se VM viene Preempted

La VM Spot può essere fermata da Google. Quando succede:

1. **Auto-restart**: systemd riavvia automaticamente il servizio (<1 min downtime)
2. **Manual restart**: `bash scripts/gcp/manage_fastapi_vm.sh start`
3. **Check logs**: `bash scripts/gcp/manage_fastapi_vm.sh logs`

---

## 📊 Monitoring Costi

### View Billing

```bash
# View current costs
gcloud billing accounts list
gcloud billing projects describe rewts-quant-trading
```

### View VMs Running

```bash
# List all VMs
gcloud compute instances list

# Expected output:
# - backtesting-api-vm: RUNNING (always-on, $3.72/mese)
# - rewts-training-spot: TERMINATED (start solo quando serve)
```

### Storage Usage

```bash
# Check storage costs
gsutil du -sh gs://rewts-trading-data
gsutil du -sh gs://rewts-trading-results
```

---

## 📈 Workflow Tipico

### Settimana 1: Training

```bash
# Lunedì: Start training
bash scripts/gcp/create_training_vm.sh
# ... SSH, train for 18h ...
gcloud compute instances stop rewts-training-spot --zone=us-central1-a

# Costo: ~$5.58
```

### Settimana 2-4: Backtesting

```python
# Backtesting API sempre disponibile
client = BacktestingClient(vm_ip="YOUR_VM_IP")

# Run 200 backtest nel mese
for ticker in tickers:
    result = client.run_backtest(...)

# Costo: $3.72 fisso (illimitati backtest)
```

### Mese totale

- Training: $5.58 × 4 = $22.32
- Backtesting: $3.72
- Storage: $3
- Gemini API: $15
- **Total: ~$44/mese**

---

## 🎯 Best Practices

### 1. Training VM
- ✅ Usa sempre Spot VM (70% sconto)
- ✅ STOP dopo training finito
- ✅ Delete se non usi per >1 settimana
- ✅ Salva modelli su GCS prima di delete

### 2. Backtesting VM
- ✅ Spot Always-On (più economico)
- ✅ Monitorare se preempted (raro)
- ✅ Systemd auto-restart configurato
- ✅ Logs per debug: `manage_fastapi_vm.sh logs`

### 3. Storage
- ✅ Lifecycle policies auto-configured
- ✅ Dati old → Nearline → Coldline
- ✅ Delete backup vecchi (>6 mesi)

### 4. Gemini API
- ✅ Pre-computa strategie mensili
- ✅ Cache responses quando possibile
- ✅ Batch requests per più ticker

### 5. Budget Alerts
- ✅ Setup alert a $50/mese
- ✅ Email notifications
- ✅ Check billing settimanalmente

---

## ⚠️ Troubleshooting

### VM Backtesting non risponde

```bash
# Check status
bash scripts/gcp/manage_fastapi_vm.sh status

# Check logs
bash scripts/gcp/manage_fastapi_vm.sh logs

# Restart
bash scripts/gcp/manage_fastapi_vm.sh restart
```

### Training VM out of memory

Edit `configs/hybrid/rewts_llm_rl.yaml`:
```yaml
rewts:
  batch_size: 32      # invece di 64
  buffer_size: 5000   # invece di 10000
```

### Spot VM preempted troppo spesso

Prova zone diversa:
```bash
# Check GPU availability
gcloud compute accelerator-types list --filter="zone:us-central1-*"

# Edit zona in create_training_vm.sh
ZONE="us-central1-b"  # invece di us-central1-a
```

### Costi troppo alti

1. Check VMs running: `gcloud compute instances list`
2. Stop training VM se non serve
3. Check storage: `gsutil du -sh gs://rewts-trading-data`
4. Delete old data
5. Verifica Gemini API usage (pre-computa strategie!)

---

## 🔐 Security

### Firewall Rules

```bash
# Restrict backtesting API to your IP only
gcloud compute firewall-rules update allow-fastapi \
  --source-ranges YOUR_IP/32

# Or allow from everywhere (default)
gcloud compute firewall-rules update allow-fastapi \
  --source-ranges 0.0.0.0/0
```

### Secrets Management

Tutti i secrets sono in Secret Manager:
- `gemini-api-key`: Gemini API
- `alpaca-api-key`: Alpaca API (optional)
- `alpaca-secret-key`: Alpaca Secret (optional)

```bash
# View secrets
gcloud secrets list

# Update secret
echo "new_key" | gcloud secrets versions add gemini-api-key --data-file=-
```

---

## 📚 Resources

- **Setup Scripts**: `scripts/gcp/`
- **Example Client**: `examples/backtesting_client_example.py`
- **FastAPI Server**: `api/fastapi_server.py`
- **Full Guide**: `GCP_Deployment_Guide.md` (dettagli completi)

---

## 🎉 Summary

### Setup (una volta)
```bash
bash scripts/gcp/setup_project.sh
bash scripts/gcp/create_buckets.sh
bash scripts/gcp/setup_secrets.sh
bash scripts/gcp/deploy_fastapi_vm.sh  # Option 2
```

### Training (quando serve)
```bash
bash scripts/gcp/create_training_vm.sh
# ... SSH, train, stop VM ...
```

### Backtesting (sempre disponibile)
```python
client = BacktestingClient(vm_ip="YOUR_VM_IP")
result = client.run_backtest(...)
```

### Costi
- **Training**: ~$5.58 per run
- **Backtesting**: $3.72/mese fisso
- **Storage**: ~$3/mese
- **Total**: ~$44/mese uso regolare

**Ottimo rapporto qualità/prezzo per sistema trading quantitativo professionale!** 🚀
