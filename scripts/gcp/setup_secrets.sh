#!/bin/bash
# Setup secrets in Google Secret Manager

set -e

echo "🔐 Setting up secrets in Google Secret Manager..."

PROJECT_ID="rewts-quant-trading"

# Create Gemini API Key secret
echo "📝 Creating Gemini API Key secret..."
read -sp "Enter your Gemini API Key: " GEMINI_KEY
echo ""

echo -n "$GEMINI_KEY" | gcloud secrets create gemini-api-key \
    --replication-policy="automatic" \
    --data-file=- 2>/dev/null || \
echo -n "$GEMINI_KEY" | gcloud secrets versions add gemini-api-key \
    --data-file=-

echo "✅ Gemini API Key saved"

# Create Alpaca API credentials (for paper trading)
echo ""
echo "📝 Creating Alpaca API credentials..."
echo "If you don't have Alpaca keys yet, press Enter to skip (you can add them later)"
read -sp "Enter your Alpaca API Key (or press Enter to skip): " ALPACA_KEY
echo ""

if [ ! -z "$ALPACA_KEY" ]; then
    echo -n "$ALPACA_KEY" | gcloud secrets create alpaca-api-key \
        --replication-policy="automatic" \
        --data-file=- 2>/dev/null || \
    echo -n "$ALPACA_KEY" | gcloud secrets versions add alpaca-api-key \
        --data-file=-

    read -sp "Enter your Alpaca Secret Key: " ALPACA_SECRET
    echo ""

    echo -n "$ALPACA_SECRET" | gcloud secrets create alpaca-secret-key \
        --replication-policy="automatic" \
        --data-file=- 2>/dev/null || \
    echo -n "$ALPACA_SECRET" | gcloud secrets versions add alpaca-secret-key \
        --data-file=-

    echo "✅ Alpaca credentials saved"
else
    echo "⏭️  Skipped Alpaca credentials (add later if needed)"
fi

# Grant access to secrets for Cloud Functions and Cloud Run
echo ""
echo "🔑 Granting access to secrets..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

if [ ! -z "$ALPACA_KEY" ]; then
    gcloud secrets add-iam-policy-binding alpaca-api-key \
        --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"

    gcloud secrets add-iam-policy-binding alpaca-secret-key \
        --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
fi

echo "✅ Secret access configured"
echo ""
echo "Secrets created:"
gcloud secrets list

echo ""
echo "To use secrets in code:"
echo '  from google.cloud import secretmanager'
echo '  client = secretmanager.SecretManagerServiceClient()'
echo '  name = f"projects/'$PROJECT_ID'/secrets/gemini-api-key/versions/latest"'
echo '  response = client.access_secret_version(request={"name": name})'
echo '  secret = response.payload.data.decode("UTF-8")'
