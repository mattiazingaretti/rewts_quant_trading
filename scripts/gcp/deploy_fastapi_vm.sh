#!/bin/bash
# Deploy FastAPI server on VM (multiple options)

set -e

echo "🚀 Deploy FastAPI Backtesting Server on GCP VM"
echo ""
echo "Choose deployment option:"
echo "  1) Always-On Standard VM (~$12/month)"
echo "  2) Always-On Spot VM (~$3.70/month) ⭐ RECOMMENDED for 24/7"
echo "  3) On-Demand Spot VM (start/stop manually, ~$0.005/hour)"
echo ""
read -p "Enter choice (1-3): " choice

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"
INSTANCE_NAME="backtesting-api-vm"
MACHINE_TYPE="e2-small"  # 2 vCPU, 2 GB RAM
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"

case $choice in
    1)
        echo "📦 Deploying Always-On Standard VM..."
        PROVISIONING_MODEL="STANDARD"
        TERMINATION_ACTION="DELETE"
        COST_ESTIMATE="~$12.40/month"
        ;;
    2)
        echo "📦 Deploying Always-On Spot VM (Recommended)..."
        PROVISIONING_MODEL="SPOT"
        TERMINATION_ACTION="STOP"
        COST_ESTIMATE="~$3.72/month"
        ;;
    3)
        echo "📦 Deploying On-Demand Spot VM..."
        PROVISIONING_MODEL="SPOT"
        TERMINATION_ACTION="STOP"
        COST_ESTIMATE="~$0.0051/hour (pay only when running)"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Configuration:"
echo "  Instance: $INSTANCE_NAME"
echo "  Machine: $MACHINE_TYPE"
echo "  Provisioning: $PROVISIONING_MODEL"
echo "  Cost: $COST_ESTIMATE"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Create firewall rule for API access
echo "🔥 Creating firewall rule..."
gcloud compute firewall-rules create allow-fastapi \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow FastAPI backtesting API" \
    --project=$PROJECT_ID 2>/dev/null || \
    echo "Firewall rule already exists"

# Create VM
echo "🖥️  Creating VM..."
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --provisioning-model=$PROVISIONING_MODEL \
    --instance-termination-action=$TERMINATION_ACTION \
    --maintenance-policy=TERMINATE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=fastapi-server \
    --metadata=startup-script='#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3-pip git

# Clone repository
cd /opt
if [ ! -d rewts_quant_trading ]; then
    git clone https://github.com/YOUR-USERNAME/rewts_quant_trading.git
fi

cd rewts_quant_trading
git pull

# Install Python dependencies
pip3 install -r requirements-inference.txt
pip3 install fastapi uvicorn[standard] python-multipart

# Get secrets from Secret Manager
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)
export GCS_BUCKET=rewts-trading-data

# Create systemd service for auto-restart
cat > /etc/systemd/system/fastapi-backtest.service <<EOF
[Unit]
Description=FastAPI Backtesting Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rewts_quant_trading
Environment="GEMINI_API_KEY=$GEMINI_API_KEY"
Environment="GCS_BUCKET=rewts-trading-data"
Environment="PORT=8000"
ExecStart=/usr/local/bin/python3 api/fastapi_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable fastapi-backtest
systemctl start fastapi-backtest

echo "✅ FastAPI server started on port 8000"
'

# Wait for VM to be ready
echo "⏳ Waiting for VM to start..."
sleep 30

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ VM created successfully!"
echo ""
echo "External IP: $EXTERNAL_IP"
echo "API URL: http://$EXTERNAL_IP:8000"
echo ""
echo "Cost estimate: $COST_ESTIMATE"
echo ""
echo "Check status:"
echo "  gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "View logs:"
echo "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u fastapi-backtest -f'"
echo ""
echo "Test API:"
echo "  curl http://$EXTERNAL_IP:8000/health"
echo ""
echo "  curl -X POST http://$EXTERNAL_IP:8000/backtest \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"ticker\": \"AAPL\", \"start_date\": \"2020-01-01\", \"end_date\": \"2020-12-31\"}'"
echo ""

if [ "$choice" = "3" ]; then
    echo "To STOP VM when not in use (save costs):"
    echo "  gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
    echo ""
    echo "To START VM when needed:"
    echo "  gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
    echo ""
fi

echo "To DELETE VM:"
echo "  gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE"
