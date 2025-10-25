# Setup Scripts - Una Tantum

Scripts da eseguire **una sola volta** all'inizio del progetto.

---

## 📋 Scripts

### 1. `01_setup_gcp_project.sh`
Setup iniziale Google Cloud Platform.

**Cosa fa**:
- Crea progetto GCP
- Abilita API necessarie (Compute, Storage, Run, etc.)
- Configura region/zone defaults
- Setup budget alerts

**Quando**: Prima volta
**Tempo**: ~5 minuti
**Costo**: $0

```bash
bash 01_setup_gcp_project.sh
```

---

### 2. `02_create_storage_buckets.sh`
Crea Cloud Storage buckets.

**Cosa fa**:
- Bucket dati e modelli (Standard → Nearline → Coldline)
- Bucket risultati (Nearline)
- Lifecycle policies automatiche

**Quando**: Dopo setup project
**Tempo**: ~2 minuti
**Costo**: $0 (storage costs start when you upload)

```bash
bash 02_create_storage_buckets.sh
```

---

### 3. `03_setup_secrets.sh`
Salva API keys in Secret Manager.

**Cosa fa**:
- Gemini API key → Secret Manager
- Alpaca API keys (optional)
- IAM permissions

**Quando**: Dopo create buckets
**Tempo**: ~2 minuti
**Costo**: $0

```bash
bash 03_setup_secrets.sh
# Will prompt for API keys
```

**Preparazione**:
- Ottieni Gemini API key da: https://makersuite.google.com/app/apikey
- (Optional) Ottieni Alpaca keys da: https://alpaca.markets

---

### 4. `04_deploy_backtesting_vm.sh`
Deploy VM Spot per backtesting API.

**Cosa fa**:
- Crea VM e2-small Spot
- Installa FastAPI server
- Configura systemd auto-restart
- Setup firewall rules

**Quando**: Dopo setup secrets
**Tempo**: ~5 minuti (+ 2 min startup)
**Costo**: $3.72/mese (Spot Always-On)

```bash
bash 04_deploy_backtesting_vm.sh

# When prompted, choose:
# 2) Spot Always-On ($3.72/month)
```

---

## 🚀 Quick Setup (All at Once)

```bash
cd scripts/setup

# Run all in sequence
bash 01_setup_gcp_project.sh
bash 02_create_storage_buckets.sh
bash 03_setup_secrets.sh
bash 04_deploy_backtesting_vm.sh
```

**Tempo totale**: ~20-30 minuti
**Costo**: $3.72/mese (solo backtesting VM)

---

## ✅ Checklist

Dopo aver completato setup, verifica:

- [ ] GCP project creato
- [ ] Budget alerts configurati
- [ ] Storage buckets esistono
- [ ] Secrets salvati in Secret Manager
- [ ] Backtesting VM running e accessibile

Verifica:
```bash
# Check project
gcloud config get-value project

# Check buckets
gsutil ls

# Check secrets
gcloud secrets list

# Check VM
cd ../utils
bash manage_vm.sh status
```

---

## 🔄 Re-run Setup?

Di solito non serve, ma se:
- Cambi progetto GCP
- Delete e ricrei infrastructure
- Setup nuovo environment (dev/prod)

Allora re-run scripts setup.

---

## 🆘 Troubleshooting

### "Billing not enabled"
Enable billing: https://console.cloud.google.com/billing/linkedaccount?project=rewts-quant-trading

### "API not enabled"
Script enables APIs automatically. If error, run:
```bash
gcloud services enable compute.googleapis.com
```

### "Secret already exists"
Update existing secret:
```bash
echo "new_key" | gcloud secrets versions add gemini-api-key --data-file=-
```

---

## 📚 Next Steps

After setup, proceed to training:
```bash
cd ../training
bash create_training_vm.sh
```

Or read: `../../QUICK_START_WORKFLOW.md`
