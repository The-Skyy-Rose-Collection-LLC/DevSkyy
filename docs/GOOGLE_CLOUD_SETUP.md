# Google Cloud Setup for DevSkyy

This guide provides instructions for setting up Google Cloud authentication and services for DevSkyy deployment.

## Prerequisites

- Google Cloud Project with billing enabled
- Appropriate IAM permissions
- Google Cloud CLI (`gcloud`) installed locally

---

## 1. Install Google Cloud CLI

### Ubuntu/Debian Linux

```bash
# Add the Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
  sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key (modern method)
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

# Update and install the Cloud SDK
sudo apt-get update && sudo apt-get install google-cloud-cli

# Verify installation
gcloud version
```

### macOS

```bash
# Via Homebrew
brew install --cask google-cloud-sdk

# Or download installer from:
# https://cloud.google.com/sdk/docs/install#mac

# Verify installation
gcloud version
```

### Windows

```powershell
# Download and run installer from:
# https://cloud.google.com/sdk/docs/install#windows

# Or via Chocolatey
choco install gcloudsdk

# Verify installation
gcloud version
```

---

## 2. Python SDK Installation

```bash
# Install Google Cloud AI Platform SDK (already done)
pip install --upgrade google-cloud-aiplatform

# Verify installation
python -c "import google.cloud.aiplatform; print('✅ Google Cloud AI Platform SDK installed')"
```

---

## 3. Authentication Setup

### Option A: Local Development (Interactive)

```bash
# Login with your Google account
gcloud auth application-default login

# This opens a browser for OAuth authentication
# After authentication, credentials are stored at:
# ~/.config/gcloud/application_default_credentials.json
```

### Option B: Service Account (CI/CD)

```bash
# Create service account
gcloud iam service-accounts create devskyy-deploy \
  --display-name="DevSkyy Deployment Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key (for local testing only)
gcloud iam service-accounts keys create ~/devskyy-sa-key.json \
  --iam-account=devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/devskyy-sa-key.json
```

### Option C: Workload Identity Federation (Recommended for GitHub Actions)

This is the **most secure** method for GitHub Actions as it doesn't require service account keys.

```bash
# 1. Enable required APIs
gcloud services enable iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com

# 2. Create Workload Identity Pool
gcloud iam workload-identity-pools create github-actions \
  --project=PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions Pool"

# 3. Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc github \
  --project=PROJECT_ID \
  --location=global \
  --workload-identity-pool=github-actions \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'The-Skyy-Rose-Collection-LLC'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 4. Get the Workload Identity Provider resource name
gcloud iam workload-identity-pools providers describe github \
  --project=PROJECT_ID \
  --location=global \
  --workload-identity-pool=github-actions \
  --format="value(name)"

# Output will be something like:
# projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github

# 5. Grant service account permissions
gcloud iam service-accounts add-iam-policy-binding \
  devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com \
  --project=PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/attribute.repository/The-Skyy-Rose-Collection-LLC/DevSkyy"
```

---

## 4. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### For Workload Identity Federation (Recommended):

```bash
# Name: GCP_WIP
# Value: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github

# Name: GCP_SA
# Value: devskyy-deploy@PROJECT_ID.iam.gserviceaccount.com

# Name: GCP_PROJECT_ID
# Value: your-project-id
```

### For Service Account Key (Not Recommended):

```bash
# Name: GCP_SA_KEY
# Value: (contents of ~/devskyy-sa-key.json)
```

---

## 5. Configure Google Cloud Project

```bash
# Set default project
gcloud config set project PROJECT_ID

# Set default region
gcloud config set run/region us-central1

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com
```

---

## 6. Verify Setup

### Test Local Authentication

```bash
# Check current authentication
gcloud auth list

# Test Cloud Run permissions
gcloud run services list --region=us-central1

# Test Storage permissions
gcloud storage ls

# Test AI Platform access
gcloud ai models list --region=us-central1
```

### Test Python SDK

```python
from google.cloud import aiplatform

# Initialize AI Platform
aiplatform.init(
    project='your-project-id',
    location='us-central1'
)

# Test connection
print("✅ Google Cloud AI Platform connected!")
```

---

## 7. Deploy DevSkyy to Cloud Run

### Manual Deployment

```bash
# Build and deploy
gcloud run deploy devskyy-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="$DATABASE_URL",SECRET_KEY="$SECRET_KEY"

# Get service URL
gcloud run services describe devskyy-api \
  --region us-central1 \
  --format='value(status.url)'
```

### Via GitHub Actions

The workflow in `.github/workflows/deploy.yml` will automatically deploy when you push to the `main` branch, using the secrets configured above.

---

## 8. Environment Variables for Cloud Run

Set these environment variables for your Cloud Run service:

```bash
gcloud run services update devskyy-api \
  --region us-central1 \
  --set-env-vars="
DATABASE_URL=postgresql://user:pass@host:5432/devskyy,
REDIS_URL=redis://host:6379/0,
SECRET_KEY=your-secret-key-here,
ENVIRONMENT=production,
ANTHROPIC_API_KEY=your-anthropic-key,
OPENAI_API_KEY=your-openai-key,
LOG_LEVEL=INFO
"
```

---

## 9. Connect to Neon Database

### Create Neon Project

1. Go to https://console.neon.tech/
2. Create new project: `devskyy-production`
3. Copy connection string

### Add to Cloud Run

```bash
# Update DATABASE_URL
gcloud run services update devskyy-api \
  --region us-central1 \
  --set-env-vars="DATABASE_URL=postgresql://user:pass@host.neon.tech:5432/devskyy"
```

---

## 10. Monitoring & Logging

### View Logs

```bash
# Stream logs
gcloud run services logs tail devskyy-api --region=us-central1

# View recent logs
gcloud run services logs read devskyy-api --region=us-central1 --limit=50
```

### Set up Alerts

```bash
# Create alert for error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="DevSkyy High Error Rate" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=60s \
  --condition-display-name="Error rate > 1%"
```

---

## 11. Cost Optimization

### Cloud Run

```bash
# Set min/max instances
gcloud run services update devskyy-api \
  --region us-central1 \
  --min-instances=0 \
  --max-instances=10

# Set CPU and memory
gcloud run services update devskyy-api \
  --region us-central1 \
  --cpu=1 \
  --memory=512Mi

# Set request timeout
gcloud run services update devskyy-api \
  --region us-central1 \
  --timeout=300
```

---

## 12. Security Best Practices

1. **Use Workload Identity Federation** instead of service account keys
2. **Enable VPC Service Controls** for production
3. **Use Secret Manager** for sensitive data
4. **Enable Cloud Armor** for DDoS protection
5. **Use Cloud CDN** for static assets
6. **Enable audit logging** for compliance
7. **Rotate credentials regularly**
8. **Use least privilege IAM roles**

---

## 13. Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check current account
gcloud auth list

# Verify permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"
```

### Deployment Failures

```bash
# Check build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log BUILD_ID

# Check service status
gcloud run services describe devskyy-api --region=us-central1
```

### Connection Issues

```bash
# Test connectivity
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://devskyy-api-HASH-uc.a.run.app/health

# Check service logs
gcloud run services logs read devskyy-api --region=us-central1
```

---

## Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Google Cloud AI Platform](https://cloud.google.com/vertex-ai/docs)
- [GitHub Actions with Google Cloud](https://github.com/google-github-actions)
- [Neon + Google Cloud](https://neon.tech/docs/guides/google-cloud-run)

---

**Last Updated:** 2025-11-17
**Maintained by:** DevSkyy Team
