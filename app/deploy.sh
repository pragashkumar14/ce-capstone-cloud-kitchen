#!/bin/bash
# Manual deployment fallback. GitHub Actions (deploy-app.yml) does this
# automatically on every push to main — use this only if you need to
# deploy without waiting on CI, or to test a local change before pushing.
set -e

BUCKET=$(cd terraform && terraform output -raw deploy_bucket_name)

echo "Zipping app/src..."
cd app/src
zip -r ../../app.zip . -x "venv/*" "__pycache__/*" "*.pyc"
cd ../..

echo "Uploading to s3://${BUCKET}/app.zip..."
aws s3 cp app.zip "s3://${BUCKET}/app.zip"

echo "Done. New instances will pick this up on next boot."
echo "To apply immediately, cycle the Auto Scaling Group's instances."
