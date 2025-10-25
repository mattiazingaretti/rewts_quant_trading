# Scripts Organization

Scripts organizzati per workflow e frequenza d'uso.

---

## 📁 Struttura

```
scripts/
├── setup/              # 🔵 Una Tantum - Setup iniziale
├── training/           # 🟢 Mensile - Training modelli
├── live/              # 🟡 Daily/Hourly - Strategie live
├── backtesting/       # 🟠 Settimanale - Review performance
├── monitoring/        # 🔴 Continuo - Monitor costi/status
├── utils/             # 🔧 Utilities
└── gcp/               # Legacy (deprecato, usa sopra)
```

---

## 🔵 setup/ - Una Tantum (Setup Iniziale)

**Quando**: All'inizio del progetto (1 volta)
**Tempo**: ~30 minuti totale
**Costo**: $0

```bash
bash scripts/setup/01_setup_gcp_project.sh       # Setup GCP project
bash scripts/setup/02_create_storage_buckets.sh  # Create buckets
bash scripts/setup/03_setup_secrets.sh           # Save API keys
bash scripts/setup/04_deploy_backtesting_vm.sh   # Deploy backtesting VM
```

📖 [Leggi setup/README.md](setup/README.md)

---

## 🟢 training/ - Mensile (Training Modelli)

**Quando**: 1 volta/mese (inizio mese)
**Tempo**: ~18 ore
**Costo**: ~$8/run

```bash
bash scripts/training/create_training_vm.sh   # Create GPU VM
# SSH into VM, then:
python scripts/training/download_data.py       # Download latest data
python scripts/training/train_rewts_llm_rl.py  # Train models
```

📖 [Leggi training/README.md](training/README.md)

---

## 🟡 live/ - Daily/Hourly (Strategie Live)

**Quando**: Ogni giorno o ogni ora
**Tempo**: Istantaneo
**Costo**: ~$0.001/call

```bash
export GEMINI_API_KEY="your_key"
python scripts/live/get_live_strategy.py --ticker AAPL    # Single
python scripts/live/get_live_strategy.py --all            # All tickers
```

📖 [Leggi live/README.md](live/README.md)

---

## 🟠 backtesting/ - Settimanale (Review Performance)

**Quando**: 1 volta/settimana (weekend)
**Tempo**: ~10 minuti
**Costo**: $0 (VM fisso)

```bash
python scripts/backtesting/run_backtest.py
```

📖 [Leggi backtesting/README.md](backtesting/README.md)

---

## 🔴 monitoring/ - Continuo (Monitor Status)

**Quando**: Giornaliero
**Tempo**: 1 minuto
**Costo**: $0

```bash
bash scripts/monitoring/check_costs.sh        # Check costs & VMs
bash scripts/utils/manage_vm.sh status        # VM status
```

📖 [Leggi monitoring/README.md](monitoring/README.md)

---

## 🔧 utils/ - Utilities

Helper scripts e utilities varie.

```bash
bash scripts/utils/manage_vm.sh status    # VM management
bash scripts/utils/manage_vm.sh logs      # View logs
bash scripts/utils/manage_vm.sh ip        # Get IP
```

📖 [Leggi utils/README.md](utils/README.md)

---

## 📅 Workflow Mensile

### Week 1: Training
```bash
# Esegui scripts/training/
bash scripts/training/create_training_vm.sh
python scripts/training/train_rewts_llm_rl.py
```

### Week 2-4: Live Trading
```bash
# Esegui scripts/live/ ogni giorno
python scripts/live/get_live_strategy.py --all
```

### Weekend: Review
```bash
# Esegui scripts/backtesting/
python scripts/backtesting/run_backtest.py

# Esegui scripts/monitoring/
bash scripts/monitoring/check_costs.sh
```

---

## 💡 Quick Start

### First Time Setup (30 min)
```bash
cd scripts/setup
bash 01_setup_gcp_project.sh
bash 02_create_storage_buckets.sh
bash 03_setup_secrets.sh
bash 04_deploy_backtesting_vm.sh
```

### Monthly Training (18h)
```bash
cd scripts/training
bash create_training_vm.sh
# SSH, download, train
```

### Daily Live Strategies (instant)
```bash
cd scripts/live
python get_live_strategy.py --all
```

---

## 📚 Documentation

- **Quick Start**: `../QUICK_START_WORKFLOW.md`
- **Full Guide**: `../TRAINING_AND_LIVE_USAGE_GUIDE.md`
- **GCP Deployment**: `../GCP_VM_Spot_Deployment.md`

---

## 🗂️ Legacy

La cartella `gcp/` è mantenuta per compatibilità ma è deprecata.
Usa le nuove cartelle organizzate per workflow.
