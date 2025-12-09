#!/bin/bash
set -e

PROJECT_ID="linklin-lab"
SERVICE_NAME="gemini-sentiment-web"
REGION="asia-east1"
MODEL_REGION="us-central1"

echo "Deploying to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Model Region: $MODEL_REGION"

gcloud config set project $PROJECT_ID

gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$REGION,MODEL_REGION=$MODEL_REGION"
