#!/bin/bash
# Create Spot VM with GPU for training

set -e

echo "🖥️  Creating Spot VM with GPU for training..."

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"
INSTANCE_NAME="rewts-training-spot"
MACHINE_TYPE="n1-standard-4"  # 4 vCPU, 15 GB RAM
GPU_TYPE="nvidia-tesla-t4"    # T4 = best cost/performance
GPU_COUNT=1

echo "Configuration:"
echo "  Instance: $INSTANCE_NAME"
echo "  Machine: $MACHINE_TYPE"
echo "  GPU: $GPU_TYPE x $GPU_COUNT"
echo "  Spot: YES (60-91% discount)"
echo "  Estimated cost: ~$0.11/hour"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Create VM
gcloud compute instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=type=$GPU_TYPE,count=$GPU_COUNT \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --maintenance-policy=TERMINATE \
  --image-family=pytorch-2-7-cu128-ubuntu-2204-nvidia-570 \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-standard \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=startup-script='#!/bin/bash
    set -e

    # Install CUDA drivers
    echo "Installing CUDA drivers..."
    /opt/deeplearning/install-driver.sh

    echo "✅ CUDA drivers installed!"
  '

echo ""
echo "⏳ Waiting for VM to be ready..."

# Wait for VM to be in RUNNING state
for i in {1..30}; do
  STATUS=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(status)')
  if [ "$STATUS" = "RUNNING" ]; then
    echo "✅ VM is running"
    break
  fi
  echo "  Waiting for VM to start... ($i/30)"
  sleep 5
done

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
  --zone=$ZONE \
  --project=$PROJECT_ID

echo "  Extracting on VM..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
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
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
  cd ~/rewts_quant_trading && \
  pip3 install -r requirements.txt && \
  pip3 install -e . && \
  echo '✅ Requirements installed!'
"

echo ""
echo "📥 Downloading data from GCS (if available)..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
  cd ~/rewts_quant_trading && \
  mkdir -p data && \
  gsutil -m cp -r gs://rewts-trading-data/raw ./data/ 2>/dev/null || echo '⚠️  No data in GCS yet'
"

echo ""
echo "✅ VM setup complete!"
echo ""
echo "Cost: ~$0.20/hour (compute) + ~$0.11/hour (T4 Spot GPU) = ~$0.31/hour"
echo ""
echo "Next steps:"
echo ""
echo "1. SSH into VM:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
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
echo "5. When done, STOP the VM to avoid charges:"
echo "   gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo ""
echo "⚠️  IMPORTANT: Spot VMs can be preempted! Use checkpointing."
