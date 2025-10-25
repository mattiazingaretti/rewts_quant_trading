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

    # Setup conda environment
    echo "Setting up Python environment..."
    su - jupyter -c "
      cd /home/jupyter

      # Clone repo (replace with your repo URL)
      if [ ! -d rewts_quant_trading ]; then
        git clone https://github.com/YOUR-USERNAME/rewts_quant_trading.git
      fi

      cd rewts_quant_trading
      git pull

      # Install requirements
      pip install -r requirements.txt

      # Download data from GCS
      gsutil -m cp -r gs://rewts-trading-data/raw ./data/ || echo \"No data in GCS yet\"

      echo \"\"
      echo \"✅ Setup complete!\"
      echo \"\"
      echo \"To start training:\"
      echo \"  1. SSH: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE\"
      echo \"  2. cd /home/jupyter/rewts_quant_trading\"
      echo \"  3. export GEMINI_API_KEY=\$(gcloud secrets versions access latest --secret=gemini-api-key)\"
      echo \"  4. python scripts/train_rewts_llm_rl.py\"
      echo \"\"
    "
  '

echo ""
echo "✅ VM created successfully!"
echo ""
echo "Cost: ~$0.20/hour (compute) + ~$0.11/hour (T4 Spot GPU) = ~$0.31/hour"
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
echo "   cd /home/jupyter/rewts_quant_trading"
echo "   export GEMINI_API_KEY=\$(gcloud secrets versions access latest --secret=gemini-api-key)"
echo "   python scripts/train_rewts_llm_rl.py"
echo ""
echo "4. Monitor training:"
echo "   watch -n 1 nvidia-smi"
echo ""
echo "5. When done, STOP the VM to avoid charges:"
echo "   gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "⚠️  IMPORTANT: Spot VMs can be preempted! Use checkpointing."
