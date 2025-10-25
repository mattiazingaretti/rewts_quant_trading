# Monitoring Scripts - Continuo

Scripts per monitorare costi, status VM e resource usage.

**Frequenza**: Giornaliero
**Tempo**: 1 minuto
**Costo**: $0

---

## 📋 Scripts

### `check_costs.sh`
Monitor completo costi e risorse GCP.

**Cosa controlla**:
- VMs running (training should be TERMINATED)
- Storage usage (data + results buckets)
- Estimated monthly costs
- Budget alerts status

**Output**:
```
💰 GCP Cost & Resource Monitor
================================

🖥️  Running VMs:
NAME                    ZONE             STATUS     MACHINE_TYPE
backtesting-api-vm      us-central1-a    RUNNING    e2-small
rewts-training-spot     us-central1-a    TERMINATED n1-standard-4

✅ Backtesting VM is running (expected, $3.72/month)

📦 Storage Usage:
  Data bucket: 142 GB
  Results bucket: 38 GB

💵 Estimated Monthly Costs:
  Backtesting VM (Spot): $3.72/month
  Storage (~180 GB): ~$3.60/month
  Gemini API (estimated): $10-50/month
  ─────────────────────────────
  TOTAL: ~$17-57/month

✅ Cost check complete
```

---

## 🚀 Usage

### Daily Check
```bash
bash check_costs.sh
```

**Do this**:
- Every morning
- Before/after training
- If API stops responding
- If unsure about costs

### Automated Monitoring
Setup cron job:
```bash
# Add to crontab
crontab -e

# Run daily at 9 AM
0 9 * * * cd /path/to/rewts_quant_trading/scripts/monitoring && bash check_costs.sh >> /tmp/gcp_monitoring.log 2>&1
```

---

## ⚠️ What to Look For

### Training VM Still Running
```
⚠️  WARNING: Training VM is RUNNING!
   This costs ~$0.31/hour. Stop it if not in use:
   gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

**Action**: STOP immediately if not training!

### High Storage Usage
```
📦 Storage Usage:
  Data bucket: 450 GB  # ⚠️ Too high
```

**Action**: Check e delete old backups/checkpoints

### Budget Exceeded
Check https://console.cloud.google.com/billing

**Action**: Review what's consuming costs

---

## 💰 Cost Thresholds

### Normal (Green)
- Backtesting VM: $3.72/month
- Storage: $2-5/month
- Gemini API: $10-20/month
- **Total**: $15-30/month

### Warning (Yellow)
- Storage > $10/month (>500 GB)
- Gemini API > $50/month (>50K calls)
- **Total**: $30-70/month

### Alert (Red)
- Training VM running >24h continuously
- Storage > $20/month (>1 TB)
- Gemini API > $100/month
- **Total**: >$100/month

**Action**: Investigate e optimize

---

## 🔍 Detailed Checks

### Check Specific VM
```bash
gcloud compute instances describe rewts-training-spot --zone=us-central1-a
```

### Check Storage Breakdown
```bash
# List all objects in bucket
gsutil ls -lh gs://rewts-trading-data/

# Check specific folder
gsutil du -sh gs://rewts-trading-data/models/
```

### Check Billing
```bash
# Get billing account
gcloud billing projects describe rewts-quant-trading

# View budget alerts
gcloud billing budgets list --billing-account=YOUR-BILLING-ACCOUNT-ID
```

### View Logs
```bash
# Cloud Run logs (backtesting API)
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Compute logs (training VM)
gcloud logging read "resource.type=gce_instance" --limit 50
```

---

## 📊 Monthly Review Checklist

End of month review:

- [ ] Run `check_costs.sh`
- [ ] Review total costs vs budget
- [ ] Check for unused resources
- [ ] Verify training VM is STOPPED
- [ ] Review storage usage trend
- [ ] Check API usage (Gemini)
- [ ] Update budget if needed
- [ ] Document any anomalies

---

## 💡 Cost Optimization Tips

### 1. Training VM
```bash
# ALWAYS stop after use
gcloud compute instances stop rewts-training-spot --zone=us-central1-a

# Verify stopped
gcloud compute instances list
```

**Savings**: $0.31/hour × unused hours

### 2. Storage
```bash
# Delete old checkpoints (keep latest only)
gsutil -m rm -r gs://rewts-trading-data/checkpoints/old/

# Move archive to Coldline
gsutil -m rewrite -s COLDLINE gs://rewts-trading-data/archive/**
```

**Savings**: 75% on archived data

### 3. Gemini API
Cache strategies instead of calling live:
```python
# Instead of calling every hour
# Call once per day and cache
```

**Savings**: 90%+ on API costs

---

## 🚨 Emergency Actions

### Costs Too High
```bash
# 1. Stop all VMs
gcloud compute instances stop --all --zone=us-central1-a

# 2. Check what's running
gcloud compute instances list

# 3. Review billing
gcloud billing projects describe rewts-quant-trading

# 4. Set budget alert
gcloud billing budgets create --budget-amount=50USD ...
```

### Training VM Won't Stop
```bash
# Force delete (last resort)
gcloud compute instances delete rewts-training-spot --zone=us-central1-a --quiet
```

### Unexpected Charges
1. Check billing: https://console.cloud.google.com/billing
2. Review resource usage
3. Check for leaked resources (load balancers, IPs, etc.)
4. Contact GCP support if needed

---

## 📚 Resources

- GCP Billing: https://console.cloud.google.com/billing
- Cost Calculator: https://cloud.google.com/products/calculator
- Pricing Docs: https://cloud.google.com/pricing

---

## 📚 Next Steps

After monitoring:
```bash
# If costs OK → continue
cd ../live
python get_live_strategy.py --all

# If costs high → optimize
# Stop unused VMs, clean storage, reduce API calls
```

Or read: `../../TRAINING_AND_LIVE_USAGE_GUIDE.md`
