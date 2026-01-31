# User Management App | Trial 3-Tier

A three-tier web application with Flask, Cloud SQL (MySQL), and a REST API. Deploy to Google Cloud Run.

## Features

- **Web UI:** Add, lookup, and delete users
- **REST API:** `GET /api/users`, `GET /api/users/<id>`, `POST /api/users`, `DELETE /api/users/<id>`
- **Cloud SQL:** Connects via Cloud SQL Python Connector or Auth Proxy
- **Deployment:** Docker + Cloud Run

## Run Locally

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your Cloud SQL credentials.

3. **Authenticate** (for Cloud SQL Connector)
   ```bash
   gcloud auth application-default login
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   Open http://localhost:8080

## Connect to Cloud SQL

### Option A: Cloud SQL Python Connector (Recommended)

Set `INSTANCE_CONNECTION_NAME` in `.env` and run `gcloud auth application-default login`.

### Option B: Cloud SQL Auth Proxy

Remove `INSTANCE_CONNECTION_NAME`, set `DB_HOST=127.0.0.1`, run the proxy:
```bash
./cloud-sql-proxy YOUR_PROJECT:REGION:INSTANCE --port=3306
```

### Option C: Direct IP

Add your IP to Cloud SQL Authorized networks, set `DB_HOST` to the instance public IP.

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List all users |
| GET | `/api/users/<id>` | Get user by ID |
| POST | `/api/users` | Create user (JSON body) |
| DELETE | `/api/users/<id>` | Delete user |

Example:
```bash
curl http://localhost:8080/api/users
```

## Deploy to GCP (Cloud Run)

1. **Set variables**
   ```bash
   export INSTANCE_CONNECTION_NAME=your-project:region:instance
   export DB_USER=appuser
   export DB_NAME=appdb
   export DB_PASS=your-password
   ```

2. **Deploy**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

Or with Cloud Build:
```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_INSTANCE_CONNECTION_NAME=proj:region:inst,_DB_USER=appuser,_DB_NAME=appdb,_DB_PASS=yourpass
```

Ensure your Cloud Run service account has **Cloud SQL Client** role.
