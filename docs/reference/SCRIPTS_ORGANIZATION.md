# Scripts Organization - New Structure

Scripts riorganizzati per workflow e frequenza d'uso.

---

## 📁 Nuova Struttura

```
scripts/
├── setup/              # 🔵 Una Tantum - Setup iniziale (30 min, $0)
│   ├── 01_setup_gcp_project.sh
│   ├── 02_create_storage_buckets.sh
│   ├── 03_setup_secrets.sh
│   ├── 04_deploy_backtesting_vm.sh
│   └── README.md
│
├── training/           # 🟢 Mensile - Training modelli (18h, $8)
│   ├── download_data.py
│   ├── train_rewts_llm_rl.py
│   ├── create_training_vm.sh
│   ├── build_docker_images.sh
│   └── README.md
│
├── live/              # 🟡 Daily/Hourly - Strategie live (instant, $0.001/call)
│   ├── get_live_strategy.py
│   └── README.md
│
├── backtesting/       # 🟠 Settimanale - Review performance (10 min, $0)
│   ├── run_backtest.py
│   └── README.md
│
├── monitoring/        # 🔴 Continuo - Monitor costi/status (1 min, $0)
│   ├── check_costs.sh
│   └── README.md
│
├── utils/            # 🔧 Utilities
│   ├── manage_vm.sh
│   └── README.md
│
├── gcp/              # 🗂️ Legacy (deprecato - usa cartelle sopra)
│   └── ...
│
└── README.md         # 📖 Main documentation
```

---

## 🆕 Cosa È Cambiato

### Prima (Disorganizzato)
```
scripts/
├── setup_project.sh
├── create_buckets.sh
├── deploy_fastapi_vm.sh
├── download_data.py
├── train_rewts_llm_rl.py
├── get_live_strategy.py
├── backtest_ensemble.py
└── gcp/
    └── ...
```
❌ Difficile capire cosa serve quando
❌ No README specifici
❌ Naming inconsistente

### Dopo (Organizzato)
```
scripts/
├── setup/              # Una tantum
├── training/           # Mensile
├── live/               # Daily
├── backtesting/        # Settimanale
├── monitoring/         # Continuo
└── utils/              # Utilities
```
✅ Chiaro per workflow
✅ README per ogni categoria
✅ Naming consistente (01_, 02_, etc.)

---

## 🎯 Come Usare

### Step 1: Setup (Una Tantum)
```bash
cd scripts/setup
bash 01_setup_gcp_project.sh
bash 02_create_storage_buckets.sh
bash 03_setup_secrets.sh
bash 04_deploy_backtesting_vm.sh
```

### Step 2: Training (Mensile)
```bash
cd scripts/training
bash create_training_vm.sh
# SSH, download, train
```

### Step 3: Live (Daily)
```bash
cd scripts/live
python get_live_strategy.py --all
```

### Step 4: Backtesting (Settimanale)
```bash
cd scripts/backtesting
python run_backtest.py
```

### Step 5: Monitoring (Daily)
```bash
cd scripts/monitoring
bash check_costs.sh
```

---

## 📋 Migration Guide

Se hai script old path hardcoded, update:

### Old Paths → New Paths

| Old | New |
|-----|-----|
| `scripts/gcp/setup_project.sh` | `scripts/setup/01_setup_gcp_project.sh` |
| `scripts/gcp/create_buckets.sh` | `scripts/setup/02_create_storage_buckets.sh` |
| `scripts/gcp/setup_secrets.sh` | `scripts/setup/03_setup_secrets.sh` |
| `scripts/gcp/deploy_fastapi_vm.sh` | `scripts/setup/04_deploy_backtesting_vm.sh` |
| `scripts/download_data.py` | `scripts/training/download_data.py` |
| `scripts/train_rewts_llm_rl.py` | `scripts/training/train_rewts_llm_rl.py` |
| `scripts/gcp/create_training_vm.sh` | `scripts/training/create_training_vm.sh` |
| `scripts/get_live_strategy.py` | `scripts/live/get_live_strategy.py` |
| `scripts/gcp/manage_fastapi_vm.sh` | `scripts/utils/manage_vm.sh` |

### Backward Compatibility

La cartella `gcp/` è mantenuta per compatibilità ma è **deprecata**.
Scripts in `gcp/` funzionano ancora ma usa le nuove cartelle per nuovi progetti.

---

## 💡 Benefits

### 1. Chiaro per Frequenza
- Setup: 1 volta
- Training: 1 volta/mese
- Live: Ogni giorno
- Backtesting: Ogni settimana
- Monitoring: Sempre

### 2. README Specifici
Ogni cartella ha il suo README con:
- Quando usare
- Come usare
- Esempi
- Troubleshooting

### 3. Naming Consistente
- Setup scripts: `01_`, `02_`, `03_` (ordine)
- Altri: nomi descrittivi

### 4. Easy Onboarding
Nuovo team member? Leggi `scripts/README.md` → clear workflow

---

## 📚 Documentation

Ogni cartella ha:
- `README.md` - Guida completa
- Scripts ben commentati
- Examples

### Leggi i README

1. **scripts/README.md** - Overview completo
2. **scripts/setup/README.md** - Setup iniziale
3. **scripts/training/README.md** - Training mensile
4. **scripts/live/README.md** - Strategie live
5. **scripts/backtesting/README.md** - Review settimanale
6. **scripts/monitoring/README.md** - Monitor costi
7. **scripts/utils/README.md** - Utilities

---

## 🔄 Update Workflow

Se aggiungi nuovo script:

1. Identifica categoria (setup/training/live/etc.)
2. Metti nella cartella giusta
3. Update README della cartella
4. Naming consistente
5. Commenta bene il codice

Example:
```bash
# Nuovo script per download news API
# → scripts/training/download_news_api.py
# → Update scripts/training/README.md
```

---

## ✅ Checklist Adoption

- [ ] Leggi `scripts/README.md`
- [ ] Leggi README specifici
- [ ] Update bookmarks/shortcuts
- [ ] Update automation scripts (cron, etc.)
- [ ] Update documentation links
- [ ] Inform team members

---

## 📖 Main Documentation

- **Quick Start**: `QUICK_START_WORKFLOW.md`
- **Full Training Guide**: `TRAINING_AND_LIVE_USAGE_GUIDE.md`
- **GCP Deployment**: `GCP_VM_Spot_Deployment.md`
- **Scripts Organization**: `SCRIPTS_ORGANIZATION.md` (questo file)

---

Ora gli script sono organizzati logicamente per workflow! 🎉
