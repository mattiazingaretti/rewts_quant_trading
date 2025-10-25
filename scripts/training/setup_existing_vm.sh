#!/bin/bash
# Setup an existing training VM with code and dependencies

set -e

echo "📦 Setting up existing training VM..."

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"
INSTANCE_NAME="rewts-training-spot"

# Set project (critical for correct VM access)
echo "Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check if VM exists and is running
echo "Checking VM status..."
STATUS=$(gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format='get(status)' 2>/dev/null || echo "NOT_FOUND")

if [ "$STATUS" = "NOT_FOUND" ]; then
  echo "❌ VM '$INSTANCE_NAME' not found in zone $ZONE"
  exit 1
fi

if [ "$STATUS" != "RUNNING" ]; then
  echo "⚠️  VM is $STATUS. Starting it..."
  gcloud compute instances start $INSTANCE_NAME --zone=$ZONE

  echo "⏳ Waiting for VM to start..."
  for i in {1..30}; do
    STATUS=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(status)')
    if [ "$STATUS" = "RUNNING" ]; then
      echo "✅ VM is running"
      break
    fi
    sleep 5
  done
fi

# Wait for SSH to be ready
echo "⏳ Waiting for SSH to be ready..."
for i in {1..30}; do
  if gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="echo 'SSH ready'" 2>/dev/null; then
    echo "✅ SSH is ready"
    break
  fi
  echo "  Waiting for SSH... ($i/30)"
  sleep 5
done

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo ""
echo "📦 Copying project files to VM..."

# Create temporary tar archive excluding unwanted files
TEMP_TAR=$(mktemp -t rewts_quant_trading.XXXXXX).tar.gz
echo "  Creating archive..."
tar -czf "$TEMP_TAR" \
  -C "$PROJECT_ROOT/.." \
  --exclude=".git" \
  --exclude="*.pyc" \
  --exclude="__pycache__" \
  --exclude="venv" \
  --exclude=".venv" \
  --exclude="*.egg-info" \
  --exclude=".pytest_cache" \
  --exclude=".mypy_cache" \
  --exclude="wandb" \
  --exclude="outputs" \
  --exclude="checkpoints" \
  --exclude="*.log" \
  --exclude=".DS_Store" \
  "$(basename $PROJECT_ROOT)"

echo "  Copying to VM..."
gcloud compute scp "$TEMP_TAR" \
  $INSTANCE_NAME:/tmp/rewts_quant_trading.tar.gz \
  --zone=$ZONE

echo "  Extracting on VM..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
  cd ~ && \
  rm -rf rewts_quant_trading && \
  tar -xzf /tmp/rewts_quant_trading.tar.gz && \
  rm /tmp/rewts_quant_trading.tar.gz && \
  echo '✅ Files extracted!'
"

# Cleanup local temp file
rm "$TEMP_TAR"
echo "✅ Files copied successfully!"

echo ""
echo "📚 Installing Python requirements on VM..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
  cd ~/rewts_quant_trading && \
  pip3 install -r requirements.txt && \
  pip3 install -e . && \
  echo '✅ Requirements installed!'
"

echo ""
echo "📥 Downloading data from GCS (if available)..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
  cd ~/rewts_quant_trading && \
  mkdir -p data && \
  gsutil -m cp -r gs://rewts-trading-data/raw ./data/ 2>/dev/null || echo '⚠️  No data in GCS yet'
"

echo ""
echo "✅ VM setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. SSH into VM:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "2. Check GPU status:"
echo "   nvidia-smi"
echo ""
echo "3. Start training:"
echo "   cd ~/rewts_quant_trading"
echo "   export GEMINI_API_KEY=\$(gcloud secrets versions access latest --secret=gemini-api-key)"
echo "   python3 scripts/training/train_rewts_llm_rl.py"
echo ""
echo "4. Monitor training:"
echo "   watch -n 1 nvidia-smi"
echo ""
