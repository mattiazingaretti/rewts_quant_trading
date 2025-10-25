#!/bin/bash
# Setup CI/CD with Cloud Build

set -e

echo "🔄 Setting up CI/CD with Cloud Build..."

PROJECT_ID="rewts-quant-trading"
GITHUB_OWNER="YOUR-GITHUB-USERNAME"  # CHANGE THIS
REPO_NAME="rewts_quant_trading"

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  GitHub: $GITHUB_OWNER/$REPO_NAME"
echo ""

# Check if GitHub repo is provided
if [ "$GITHUB_OWNER" = "YOUR-GITHUB-USERNAME" ]; then
    echo "❌ Please edit this script and set GITHUB_OWNER to your GitHub username"
    exit 1
fi

# Enable Cloud Build API
echo "🔧 Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Grant Cloud Build permissions
echo "🔑 Granting Cloud Build permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Create build trigger
echo ""
echo "📋 Creating Cloud Build trigger..."
echo ""
echo "Please follow these steps to connect your GitHub repo:"
echo ""
echo "1. Visit: https://console.cloud.google.com/cloud-build/triggers/connect?project=$PROJECT_ID"
echo "2. Select 'GitHub (Cloud Build GitHub App)'"
echo "3. Authenticate with GitHub"
echo "4. Select repository: $GITHUB_OWNER/$REPO_NAME"
echo "5. Create a trigger with these settings:"
echo "   - Name: deploy-on-push"
echo "   - Event: Push to a branch"
echo "   - Branch: ^main$"
echo "   - Configuration: cloudbuild.yaml"
echo ""
read -p "Press Enter when you've created the trigger..."

echo ""
echo "✅ CI/CD setup complete!"
echo ""
echo "How it works:"
echo "  1. Push code to main branch"
echo "  2. Cloud Build automatically:"
echo "     - Builds Docker images"
echo "     - Pushes to GCR"
echo "     - Deploys backtesting API to Cloud Run"
echo ""
echo "View builds: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
echo ""
echo "Cost: ~$0.003 per build minute (first 120 minutes/day are free)"
