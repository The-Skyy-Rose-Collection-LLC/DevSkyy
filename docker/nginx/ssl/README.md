# SSL Certificate Setup

## For Development/Testing (Self-Signed Certificate)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=DevSkyy/CN=localhost"
```

## For Production (Let's Encrypt)

### Option 1: Using Certbot

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Copy certificates to docker volume
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./fullchain.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./privkey.pem
```

### Option 2: Using Docker Certbot

```bash
# Create certbot configuration
docker run -it --rm --name certbot \
  -v "$PWD/docker/nginx/ssl:/etc/letsencrypt" \
  -v "$PWD/certbot-webroot:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d your-domain.com \
  -d www.your-domain.com
```

### Auto-Renewal Setup

Add to crontab (replace `/path/to/devskyy` with your actual project path):
```bash
0 0 * * * docker run --rm --name certbot -v "/path/to/devskyy/docker/nginx/ssl:/etc/letsencrypt" -v "/path/to/devskyy/certbot-webroot:/var/www/certbot" certbot/certbot renew && cd /path/to/devskyy && docker-compose -f docker-compose.prod.yml restart nginx
```

Or create a renewal script `/usr/local/bin/renew-devskyy-certs.sh`:
```bash
#!/bin/bash
PROJECT_DIR="/path/to/devskyy"
docker run --rm --name certbot \
  -v "${PROJECT_DIR}/docker/nginx/ssl:/etc/letsencrypt" \
  -v "${PROJECT_DIR}/certbot-webroot:/var/www/certbot" \
  certbot/certbot renew && \
cd "${PROJECT_DIR}" && \
docker-compose -f docker-compose.prod.yml restart nginx
```

Then add to crontab:
```bash
0 0 * * * /usr/local/bin/renew-devskyy-certs.sh >> /var/log/certbot-renewal.log 2>&1
```

## Required Files

- `fullchain.pem`: Full certificate chain
- `privkey.pem`: Private key

## Security Notes (Truth Protocol Rule #13)

1. Never commit private keys to version control
2. Set proper file permissions: `chmod 600 privkey.pem`
3. Rotate certificates before expiration (90 days for Let's Encrypt)
4. Use strong key sizes (minimum 2048-bit RSA)
5. Enable OCSP stapling for revocation checking
