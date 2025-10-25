#!/bin/bash
# Create Cloud Storage buckets for ReWTSE-LLM-RL

set -e

echo "🗄️  Creating Cloud Storage buckets..."

PROJECT_ID="rewts-quant-trading"
REGION="us-central1"

# Bucket for training data and models (Standard storage)
BUCKET_DATA="gs://rewts-trading-data"
echo "Creating $BUCKET_DATA..."
if gsutil ls $BUCKET_DATA 2>/dev/null; then
    echo "✅ Bucket already exists"
else
    gsutil mb -c STANDARD -l $REGION $BUCKET_DATA
    echo "✅ Data bucket created"
fi

# Bucket for results and archives (Nearline storage - cheaper)
BUCKET_RESULTS="gs://rewts-trading-results"
echo "Creating $BUCKET_RESULTS..."
if gsutil ls $BUCKET_RESULTS 2>/dev/null; then
    echo "✅ Bucket already exists"
else
    gsutil mb -c NEARLINE -l $REGION $BUCKET_RESULTS
    echo "✅ Results bucket created"
fi

# Set lifecycle policy to automatically move old data to Coldline
echo "📋 Setting up lifecycle policies..."
cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "NEARLINE"
        },
        "condition": {
          "age": 30,
          "matchesStorageClass": ["STANDARD"]
        }
      },
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "COLDLINE"
        },
        "condition": {
          "age": 90,
          "matchesStorageClass": ["NEARLINE"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json $BUCKET_DATA
echo "✅ Lifecycle policy set for data bucket"

# Create folder structure
echo "📁 Creating folder structure..."
echo "" | gsutil cp - $BUCKET_DATA/raw/.keep
echo "" | gsutil cp - $BUCKET_DATA/processed/.keep
echo "" | gsutil cp - $BUCKET_DATA/models/.keep
echo "" | gsutil cp - $BUCKET_DATA/checkpoints/.keep
echo "" | gsutil cp - $BUCKET_DATA/strategies/.keep
echo "" | gsutil cp - $BUCKET_RESULTS/metrics/.keep
echo "" | gsutil cp - $BUCKET_RESULTS/visualizations/.keep

echo "✅ Storage setup complete!"
echo ""
echo "Buckets created:"
echo "  - $BUCKET_DATA (Standard → Nearline → Coldline)"
echo "  - $BUCKET_RESULTS (Nearline)"
echo ""
echo "Cost estimate:"
echo "  - 100 GB in data bucket: ~$2/month"
echo "  - 50 GB in results bucket: ~$0.50/month"
