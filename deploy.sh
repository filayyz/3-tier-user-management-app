#!/bin/bash
# Deploy User Management App to Google Cloud Run
# Prerequisites: gcloud CLI, Docker, Cloud SQL instance

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="user-management-app"

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Database: SQLite (no Cloud SQL needed)"

# Grant Cloud Build permissions
echo "Setting up IAM permissions and APIs..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com sqladmin.googleapis.com

# Grant to Cloud Build service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/editor" 2>/dev/null || true

# Grant to Compute Engine service account (the one actually running the build)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/editor" 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter" 2>/dev/null || true

echo "Waiting for IAM propagation..."
sleep 15

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

# Deploy to Cloud Run with Cloud SQL connection
# Set DB_PASS via: export DB_PASS=yourpassword
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "USE_SQLITE=1,SQLITE_DB=/tmp/users.db"

echo "Deployed! Get URL with: gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'"
