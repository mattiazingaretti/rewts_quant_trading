# Utils Scripts

Utility scripts per gestione VM e operazioni comuni.

---

## 📋 Scripts

### `manage_vm.sh`
Gestione completa backtesting VM.

**Commands**:
- `status` - Check VM status e service
- `start` - Start VM
- `stop` - Stop VM (save costs)
- `restart` - Restart VM
- `logs` - View FastAPI logs
- `ip` - Get external IP
- `delete` - Delete VM completely

---

## 🚀 Usage

### Check Status
```bash
bash manage_vm.sh status
```

**Output**:
```
📊 VM Status:
NAME                ZONE           STATUS  MACHINE_TYPE  EXTERNAL_IP
backtesting-api-vm  us-central1-a  RUNNING e2-small      35.123.45.67

Service status:
● fastapi-backtest.service - FastAPI Backtesting Server
   Active: active (running)
```

### Get IP
```bash
bash manage_vm.sh ip
```

**Output**:
```
External IP: 35.123.45.67
API URL: http://35.123.45.67:8000
Docs: http://35.123.45.67:8000/docs
```

### View Logs
```bash
bash manage_vm.sh logs
```

**Output** (real-time):
```
📋 FastAPI Logs (Ctrl+C to exit):
Jan 25 10:15:32 backtesting-api-vm python3[1234]: INFO: Started server process [1234]
Jan 25 10:15:32 backtesting-api-vm python3[1234]: INFO: Waiting for application startup.
Jan 25 10:23:45 backtesting-api-vm python3[1234]: 📊 Running backtest for AAPL...
Jan 25 10:24:12 backtesting-api-vm python3[1234]: ✅ Completed - Sharpe: 1.45
```

### Stop VM
```bash
bash manage_vm.sh stop
```

**Use when**: Non usi backtesting per periodo prolungato (>1 settimana)
**Savings**: $3.72/mese

### Start VM
```bash
bash manage_vm.sh start
```

**Wait**: 2-3 minuti for startup

### Restart VM
```bash
bash manage_vm.sh restart
```

**Use when**: API not responding, after updates

### Delete VM
```bash
bash manage_vm.sh delete
```

**Warning**: Permanent! Re-deploy con `scripts/setup/04_deploy_backtesting_vm.sh`

---

## 📚 Common Tasks

### Quick Health Check
```bash
bash manage_vm.sh status
bash manage_vm.sh ip
curl http://$(bash manage_vm.sh ip | grep "External IP" | cut -d: -f2 | tr -d ' ')/health
```

### Debug API Issues
```bash
# 1. Check VM is running
bash manage_vm.sh status

# 2. View logs for errors
bash manage_vm.sh logs

# 3. Restart if needed
bash manage_vm.sh restart

# 4. Test API
curl http://YOUR_VM_IP:8000/health
```

### Monitor Live
```bash
# Watch logs in real-time
bash manage_vm.sh logs

# In another terminal, send requests
curl -X POST http://YOUR_VM_IP:8000/backtest ...
```

---

## 📚 Next Steps

Main workflow scripts:
- Setup: `scripts/setup/README.md`
- Training: `scripts/training/README.md`
- Live: `scripts/live/README.md`
- Backtesting: `scripts/backtesting/README.md`
- Monitoring: `scripts/monitoring/README.md`
