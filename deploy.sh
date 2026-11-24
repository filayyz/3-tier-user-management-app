#!/bin/bash
# Build the Docker image, then run it locally or deploy it to Cloud Run.
#   ./deploy.sh -local
#   ./deploy.sh -cloud

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

IMAGE_LOCAL="user-management-app:local"
CONTAINER_NAME="user-management-app"
PORT="${PORT:-8080}"

usage() {
  echo "Usage: $0 -local | -cloud"
  echo "  -local   Build the Docker image and run it on this machine"
  echo "  -cloud   Build the Docker image locally and deploy it to Cloud Run"
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required. Install Docker Desktop, then retry."
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but the daemon is not running. Start Docker Desktop, then retry."
    exit 1
  fi
}

build_image() {
  local tag="$1"
  local platform="${2:-}"
  if [ -n "$platform" ]; then
    echo "Building image: $tag ($platform)"
    # Cloud Run only runs linux/amd64. Disable provenance so the push is a
    # single image manifest, not an OCI index that Cloud Run rejects.
    docker build --platform "$platform" --provenance=false --sbom=false -t "$tag" .
  else
    echo "Building image: $tag"
    docker build -t "$tag" .
  fi
}

run_local() {
  require_docker
  build_image "$IMAGE_LOCAL"

  mkdir -p "$ROOT/data"

  if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f "$CONTAINER_NAME" >/dev/null
  fi

  echo "Running container on http://localhost:$PORT"
  echo "SQLite data is stored in ./data/local.db"
  docker run --rm --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -e PORT=8080 \
    -e USE_SQLITE=1 \
    -e SQLITE_DB=/app/data/local.db \
    -v "$ROOT/data:/app/data" \
    "$IMAGE_LOCAL"
}

deploy_cloud() {
  require_docker

  if ! command -v gcloud >/dev/null 2>&1; then
    echo "gcloud is required for -cloud. Install the Google Cloud SDK, then retry."
    exit 1
  fi

  local project_id region service_name repo_name image_remote
  project_id=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
  region=${GCP_REGION:-us-central1}
  service_name="user-management-app"
  repo_name="user-management"
  image_remote="${region}-docker.pkg.dev/${project_id}/${repo_name}/${service_name}"

  if [ -z "$project_id" ] || [ "$project_id" = "(unset)" ]; then
    echo "No GCP project is set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
  fi

  echo "Project: $project_id"
  echo "Region: $region"
  echo "Service: $service_name"
  echo "Staying on Always Free: Cloud Run + Artifact Registry + SQLite (no Cloud SQL)"

  echo "Enabling required APIs..."
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com

  if ! gcloud artifacts repositories describe "$repo_name" --location="$region" >/dev/null 2>&1; then
    echo "Creating Artifact Registry repo: $repo_name"
    gcloud artifacts repositories create "$repo_name" \
      --repository-format=docker \
      --location="$region" \
      --description="User management app images"
  fi

  build_image "$image_remote" linux/amd64

  echo "Configuring Docker to push to Artifact Registry..."
  gcloud auth configure-docker "${region}-docker.pkg.dev" --quiet

  echo "Pushing image: $image_remote"
  docker push "$image_remote"

  echo "Deploying to Cloud Run (scale to zero, 1 instance max, CPU only while serving)..."
  gcloud run deploy "$service_name" \
    --image "$image_remote" \
    --platform managed \
    --region "$region" \
    --allow-unauthenticated \
    --cpu=1 \
    --memory=512Mi \
    --min-instances=0 \
    --max-instances=1 \
    --cpu-throttling \
    --timeout=60 \
    --clear-cloudsql-instances \
    --clear-vpc-connector \
    --set-env-vars "USE_SQLITE=1,SQLITE_DB=/tmp/users.db"

  echo "Deployed. Get the URL with:"
  echo "  gcloud run services describe $service_name --region $region --format='value(status.url)'"
  echo
  echo "This stays within Always Free if traffic stays low. GCP still requires a billing"
  echo "account and will charge if you exceed free limits or create Cloud SQL / VMs."
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

case "$1" in
  -local)
    run_local
    ;;
  -cloud)
    deploy_cloud
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown option: $1"
    usage
    exit 1
    ;;
esac
