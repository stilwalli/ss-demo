#!/bin/bash
set -e
PROJECT_ID="gcex-contact-center-508117"
REGION="us-central1"
SERVICE_NAME="statestreet-portal-api"

cd /usr/local/google/home/stilwalli/mywork/statestreet_fastapi
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID="$PROJECT_ID",DATABASE_ID="statestreet" \
  --quiet
