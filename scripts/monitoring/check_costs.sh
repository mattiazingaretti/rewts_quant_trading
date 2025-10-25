#!/bin/bash
# Check GCP costs and resource usage

set -e

PROJECT_ID="rewts-quant-trading"

echo "💰 GCP Cost & Resource Monitor"
echo "================================"
echo ""

# Check running VMs
echo "🖥️  Running VMs:"
gcloud compute instances list --format="table(name,zone,status,machineType)"
echo ""

# Check if training VM is running (should be TERMINATED)
TRAINING_STATUS=$(gcloud compute instances describe rewts-training-spot --zone=us-central1-a --format="get(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$TRAINING_STATUS" = "RUNNING" ]; then
    echo "⚠️  WARNING: Training VM is RUNNING!"
    echo "   This costs ~$0.31/hour. Stop it if not in use:"
    echo "   gcloud compute instances stop rewts-training-spot --zone=us-central1-a"
    echo ""
fi

# Check backtesting VM
BACKTEST_STATUS=$(gcloud compute instances describe backtesting-api-vm --zone=us-central1-a --format="get(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$BACKTEST_STATUS" = "RUNNING" ]; then
    echo "✅ Backtesting VM is running (expected, $3.72/month)"
else
    echo "⚠️  Backtesting VM is not running"
fi
echo ""

# Check storage usage
echo "📦 Storage Usage:"
echo "  Data bucket:"
gsutil du -sh gs://rewts-trading-data 2>/dev/null || echo "  Bucket not found"
echo "  Results bucket:"
gsutil du -sh gs://rewts-trading-results 2>/dev/null || echo "  Bucket not found"
echo ""

# Estimate monthly costs
echo "💵 Estimated Monthly Costs:"
echo "  Backtesting VM (Spot): $3.72/month"

if [ "$TRAINING_STATUS" = "RUNNING" ]; then
    HOURS_RUNNING=$(gcloud compute instances describe rewts-training-spot --zone=us-central1-a --format="get(lastStartTimestamp)" 2>/dev/null)
    echo "  Training VM: Currently RUNNING - $0.31/hour"
fi

echo "  Storage (~150 GB): ~$3/month"
echo "  Gemini API (estimated): $10-50/month"
echo "  ─────────────────────────────"
echo "  TOTAL: ~$17-57/month"
echo ""

# View billing
echo "💳 View detailed billing:"
echo "  https://console.cloud.google.com/billing?project=$PROJECT_ID"
echo ""

# Budget alerts
echo "🔔 Budget Alerts:"
gcloud billing budgets list --billing-account=$(gcloud billing projects describe $PROJECT_ID --format="get(billingAccountName)" | cut -d'/' -f2) 2>/dev/null || echo "  No budget alerts configured"
echo ""

echo "✅ Cost check complete"
