#!/bin/bash
# Setup GCP project for ReWTSE-LLM-RL

set -e  # Exit on error

echo "🚀 Setting up GCP Project for ReWTSE-LLM-RL..."

# Configuration
PROJECT_ID="rewts-quant-trading"
PROJECT_NAME="ReWTSE Trading System"
REGION="us-central1"
ZONE="us-central1-a"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Login to GCP
echo "📝 Logging in to GCP..."
gcloud auth login

# Create project (if not exists)
echo "📦 Creating project $PROJECT_ID..."
if gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo "✅ Project $PROJECT_ID already exists"
else
    gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"
    echo "✅ Project created"
fi

# Set default project
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Link billing account (you'll need to do this manually if not already linked)
echo ""
echo "⚠️  IMPORTANT: Link a billing account to your project"
echo "   Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo ""
read -p "Press Enter when billing is enabled..."

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

echo "✅ All APIs enabled"

# Setup budget alert
echo "💰 Setting up budget alerts..."
echo ""
echo "To setup budget alerts, visit:"
echo "https://console.cloud.google.com/billing/budgets?project=$PROJECT_ID"
echo ""
echo "Recommended budget: $100/month with alerts at 50%, 90%, 100%"
echo ""

echo "✅ GCP Project setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run: bash scripts/gcp/create_buckets.sh"
echo "  2. Run: bash scripts/gcp/setup_secrets.sh"
echo "  3. Run: bash scripts/gcp/build_and_push.sh"
