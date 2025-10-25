#!/bin/bash
# Build and push Docker images to GCR

set -e

echo "🐳 Building and pushing Docker images to GCR..."

PROJECT_ID="rewts-quant-trading"

# Configure Docker for GCR
echo "🔧 Configuring Docker authentication..."
gcloud auth configure-docker

# Build training image
echo ""
echo "📦 Building training image..."
docker build -f docker/Dockerfile.training \
  -t gcr.io/$PROJECT_ID/training:latest \
  -t gcr.io/$PROJECT_ID/training:$(git rev-parse --short HEAD) \
  .

echo "✅ Training image built"

# Build backtesting image
echo ""
echo "📦 Building backtesting image..."
docker build -f docker/Dockerfile.backtesting \
  -t gcr.io/$PROJECT_ID/backtesting:latest \
  -t gcr.io/$PROJECT_ID/backtesting:$(git rev-parse --short HEAD) \
  .

echo "✅ Backtesting image built"

# Push images to GCR
echo ""
echo "⬆️  Pushing images to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/training:latest
docker push gcr.io/$PROJECT_ID/training:$(git rev-parse --short HEAD)
docker push gcr.io/$PROJECT_ID/backtesting:latest
docker push gcr.io/$PROJECT_ID/backtesting:$(git rev-parse --short HEAD)

echo ""
echo "✅ All images pushed to GCR!"
echo ""
echo "Images available:"
echo "  - gcr.io/$PROJECT_ID/training:latest"
echo "  - gcr.io/$PROJECT_ID/backtesting:latest"
echo ""
echo "Next steps:"
echo "  1. Deploy backtesting: bash scripts/gcp/deploy_backtesting.sh"
echo "  2. Create training VM: bash scripts/gcp/create_training_vm.sh"
