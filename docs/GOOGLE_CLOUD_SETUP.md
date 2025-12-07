# Google Cloud Platform Setup Guide

Complete guide for deploying DevSkyy to Google Cloud Platform using Cloud Run, Cloud SQL, and other GCP services.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Project created** in Google Cloud Console
4. **APIs enabled**:
   - Cloud Run API
   - Cloud SQL Admin API
   - Secret Manager API
   - Container Registry API
   - Cloud Build API
   - Cloud Monitoring API

## Initial Setup

### 1. Install gcloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# Download from https://cloud.google.com/sdk/docs/install

# Initialize gcloud
gcloud init
```

### 2. Create Project

```bash
# Set project variables
export PROJECT_ID="devskyy-production"
export REGION="us-central1"
export ZONE="us-central1-a"

# Create project
gcloud projects create $PROJECT_ID --name="DevSkyy Production"

# Set active project
gcloud config set project $PROJECT_ID

# Link billing account (required)
gcloud beta billing accounts list
gcloud beta billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### 3. Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudscheduler.googleapis.com
```

## Database Setup (Cloud SQL)

### 1. Create PostgreSQL Instance

```bash
# Create Cloud SQL instance
gcloud sql instances create devskyy-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-16384 \
  --region=$REGION \
  --availability-type=REGIONAL \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --storage-type=SSD \
  --storage-size=500GB \
  --storage-auto-increase \
  --database-flags=max_connections=200,shared_buffers=4GB

# Set root password
gcloud sql users set-password postgres \
  --instance=devskyy-postgres \
  --password=$(openssl rand -base64 32)

# Create application database
gcloud sql databases create devskyy \
  --instance=devskyy-postgres \
  --charset=UTF8

# Create application user
gcloud sql users create devskyy_app \
  --instance=devskyy-postgres \
  --password=$(openssl rand -base64 32)
```

### 2. Get Connection String

```bash
# Get instance connection name
gcloud sql instances describe devskyy-postgres \
  --format='value(connectionName)'

# Connection string format:
# postgresql://devskyy_app:PASSWORD@/devskyy?host=/cloudsql/CONNECTION_NAME
```

## Redis Setup (Memorystore)

### 1. Create Redis Instance

```bash
# Create Memorystore Redis instance
gcloud redis instances create devskyy-redis \
  --size=5 \
  --region=$REGION \
  --redis-version=redis_7_0 \
  --tier=standard \
  --redis-config maxmemory-policy=allkeys-lru

# Get Redis host and port
gcloud redis instances describe devskyy-redis \
  --region=$REGION \
  --format='value(host,port)'

# Connection string format:
# redis://HOST:PORT/0
```

## Secret Management

### 1. Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create devskyy-secret-key --data-file=-

echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create devskyy-jwt-secret --data-file=-

echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create devskyy-encryption-key --data-file=-

# Store database URL
echo -n "postgresql://devskyy_app:PASSWORD@/devskyy?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets create devskyy-database-url --data-file=-

# Store Redis URL
echo -n "redis://REDIS_HOST:6379/0" | \
  gcloud secrets create devskyy-redis-url --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding devskyy-secret-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Repeat for all secrets
```

### 2. List Secrets

```bash
# List all secrets
gcloud secrets list

# Get secret value
gcloud secrets versions access latest --secret="devskyy-secret-key"
```

## Build and Deploy

### 1. Build Container Image

```bash
# Build with Cloud Build
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/devskyy:latest \
  --timeout=30m \
  .

# Or build locally and push
docker build -t gcr.io/$PROJECT_ID/devskyy:latest -f Dockerfile.production .
docker push gcr.io/$PROJECT_ID/devskyy:latest
```

### 2. Deploy to Cloud Run

```bash
# Deploy Cloud Run service
gcloud run deploy devskyy \
  --image gcr.io/$PROJECT_ID/devskyy:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 2 \
  --memory 4Gi \
  --min-instances 1 \
  --max-instances 20 \
  --concurrency 100 \
  --timeout 300 \
  --set-env-vars "ENVIRONMENT=production" \
  --set-secrets "SECRET_KEY=devskyy-secret-key:latest,JWT_SECRET_KEY=devskyy-jwt-secret:latest,ENCRYPTION_MASTER_KEY=devskyy-encryption-key:latest,DATABASE_URL=devskyy-database-url:latest,REDIS_URL=devskyy-redis-url:latest" \
  --add-cloudsql-instances $PROJECT_ID:$REGION:devskyy-postgres

# Get service URL
gcloud run services describe devskyy \
  --region $REGION \
  --format 'value(status.url)'
```

### 3. Run Database Migrations

```bash
# Create Cloud Run job for migrations
gcloud run jobs create devskyy-migrate \
  --image gcr.io/$PROJECT_ID/devskyy:latest \
  --region $REGION \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,ENVIRONMENT=production" \
  --task-timeout=600 \
  --command python \
  --args "manage.py,migrate,--noinput"

# Execute migration job
gcloud run jobs execute devskyy-migrate --region $REGION --wait
```

## Custom Domain Setup

### 1. Map Custom Domain

```bash
# Verify domain ownership first in Cloud Console

# Map domain to Cloud Run service
gcloud run domain-mappings create \
  --service devskyy \
  --domain api.devskyy.com \
  --region $REGION

# Get DNS records to configure
gcloud run domain-mappings describe \
  --domain api.devskyy.com \
  --region $REGION
```

### 2. Configure DNS

Add the provided DNS records to your domain registrar:

```
Type: A
Name: api
Value: 216.239.32.21

Type: AAAA
Name: api
Value: 2001:4860:4802:32::15

Type: CNAME
Name: www
Value: ghs.googlehosted.com
```

## Monitoring and Logging

### 1. Enable Cloud Monitoring

```bash
# Monitoring is automatically enabled for Cloud Run

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=devskyy" \
  --limit 50 \
  --format json

# Tail logs
gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=devskyy"
```

### 2. Create Monitoring Alerts

**FIXED: Added --condition-filter flag and corrected --condition-duration flag**

```bash
# Create alert policy for error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="DevSkyy High Error Rate" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=1.0 \
  --condition-threshold-duration=300s \
  --condition-filter='metric.type="run.googleapis.com/request_count" AND resource.type="cloud_run_revision" AND resource.labels.service_name="devskyy" AND metric.labels.response_code_class="5xx"'

# Create alert policy for latency
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="DevSkyy High Latency" \
  --condition-display-name="P95 latency > 200ms" \
  --condition-threshold-value=200.0 \
  --condition-duration=300s \
  --condition-filter='metric.type="run.googleapis.com/request_latencies" AND resource.type="cloud_run_revision" AND resource.labels.service_name="devskyy"'
```

### 3. Set Up Notification Channels

```bash
# Create email notification channel
gcloud alpha monitoring channels create \
  --display-name="DevOps Team Email" \
  --type=email \
  --channel-labels=email_address=devops@devskyy.com

# Create Slack notification channel
gcloud alpha monitoring channels create \
  --display-name="DevOps Slack" \
  --type=slack \
  --channel-labels=channel_name=#devops,url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Load Balancer Setup (Optional)

### 1. Create Load Balancer

```bash
# Reserve static IP
gcloud compute addresses create devskyy-ip \
  --global

# Create backend service
gcloud compute backend-services create devskyy-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED

# Add Cloud Run NEG
gcloud compute network-endpoint-groups create devskyy-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=devskyy

gcloud compute backend-services add-backend devskyy-backend \
  --global \
  --network-endpoint-group=devskyy-neg \
  --network-endpoint-group-region=$REGION

# Create URL map
gcloud compute url-maps create devskyy-lb \
  --default-service devskyy-backend

# Create SSL certificate
gcloud compute ssl-certificates create devskyy-cert \
  --domains=api.devskyy.com

# Create HTTPS proxy
gcloud compute target-https-proxies create devskyy-https-proxy \
  --url-map=devskyy-lb \
  --ssl-certificates=devskyy-cert

# Create forwarding rule
gcloud compute forwarding-rules create devskyy-https-rule \
  --global \
  --target-https-proxy=devskyy-https-proxy \
  --address=devskyy-ip \
  --ports=443
```

## Scheduled Jobs (Cloud Scheduler)

### 1. Create Scheduled Tasks

```bash
# Create cleanup job
gcloud scheduler jobs create http cleanup-job \
  --location=$REGION \
  --schedule="0 2 * * *" \
  --uri="https://api.devskyy.com/admin/cleanup" \
  --http-method=POST \
  --headers="Authorization=Bearer $ADMIN_TOKEN"

# Create backup job
gcloud scheduler jobs create http backup-job \
  --location=$REGION \
  --schedule="0 3 * * *" \
  --uri="https://api.devskyy.com/admin/backup" \
  --http-method=POST \
  --headers="Authorization=Bearer $ADMIN_TOKEN"
```

## CI/CD Integration

### 1. Create Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# Add to GitHub Secrets as GCP_SA_KEY
cat github-actions-key.json | base64
```

## Cost Optimization

### 1. Set Resource Limits

```bash
# Update Cloud Run service with cost controls
gcloud run services update devskyy \
  --region $REGION \
  --min-instances 0 \
  --max-instances 10 \
  --cpu-throttling \
  --cpu-boost
```

### 2. Enable Budget Alerts

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="DevSkyy Monthly Budget" \
  --budget-amount=1000USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Backup and Disaster Recovery

### 1. Automated Database Backups

```bash
# Backups are automatic, configure retention
gcloud sql instances patch devskyy-postgres \
  --backup-start-time=03:00 \
  --retained-backups-count=30

# Create manual backup
gcloud sql backups create \
  --instance=devskyy-postgres \
  --description="Manual backup before major deployment"
```

### 2. Export Database

```bash
# Export to Cloud Storage
gcloud sql export sql devskyy-postgres \
  gs://devskyy-backups/database-$(date +%Y%m%d).sql \
  --database=devskyy

# Import from Cloud Storage
gcloud sql import sql devskyy-postgres \
  gs://devskyy-backups/database-20251118.sql \
  --database=devskyy
```

## Security Best Practices

### 1. Enable VPC Connector (Recommended)

```bash
# Create VPC connector for Cloud Run
gcloud compute networks vpc-access connectors create devskyy-connector \
  --region=$REGION \
  --range=10.8.0.0/28

# Update Cloud Run to use VPC
gcloud run services update devskyy \
  --region $REGION \
  --vpc-connector devskyy-connector \
  --vpc-egress private-ranges-only
```

### 2. Configure Cloud Armor (DDoS Protection)

```bash
# Create security policy
gcloud compute security-policies create devskyy-policy \
  --description="DDoS and application security"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=devskyy-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600

# Attach to backend service
gcloud compute backend-services update devskyy-backend \
  --global \
  --security-policy=devskyy-policy
```

## Troubleshooting

### View Service Logs

```bash
# Real-time logs
gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=devskyy"

# Filter errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=devskyy AND severity>=ERROR" \
  --limit 100 \
  --format json
```

### Debug Deployment Issues

```bash
# Check service status
gcloud run services describe devskyy --region $REGION

# View revisions
gcloud run revisions list --service devskyy --region $REGION

# Rollback to previous revision
gcloud run services update-traffic devskyy \
  --region $REGION \
  --to-revisions=REVISION_NAME=100
```

### Test Database Connection

```bash
# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:devskyy-postgres=tcp:5432

# Test connection
psql postgresql://devskyy_app:PASSWORD@localhost:5432/devskyy
```

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Best Practices for Cloud Run](https://cloud.google.com/run/docs/tips)
