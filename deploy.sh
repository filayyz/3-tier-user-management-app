#!/bin/bash
# Deploy User Management App to Google Cloud Run
# Prerequisites: gcloud CLI, Docker, Cloud SQL instance

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="user-management-app"

# Get these from your .env or Cloud SQL Console
INSTANCE_CONNECTION_NAME=${INSTANCE_CONNECTION_NAME:-"YOUR_PROJECT:YOUR_REGION:YOUR_INSTANCE"}
DB_USER=${DB_USER:-appuser}
DB_NAME=${DB_NAME:-appdb}

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

# Deploy to Cloud Run with Cloud SQL connection
# Set DB_PASS via: export DB_PASS=yourpassword
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --set-env-vars "INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_USER=$DB_USER,DB_NAME=$DB_NAME,DB_PASS=$DB_PASS"

echo "Deployed! Get URL with: gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'"
