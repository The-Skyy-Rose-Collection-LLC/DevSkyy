# Vercel Domain Setup Guide for app.devskyy.app

This guide walks you through configuring the custom domain `app.devskyy.app` for the DevSkyy Next.js frontend on Vercel.

---

## Prerequisites

1. **Vercel Account**: Ensure you have a Vercel account and the DevSkyy project connected
2. **Domain Access**: You must have access to the DNS settings for `devskyy.app`
3. **Vercel CLI** (optional): Install with `npm install -g vercel`

---

## Step 1: Configure Environment Variables in Vercel

Before adding the domain, configure production environment variables:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your DevSkyy project
3. Navigate to **Settings → Environment Variables**
4. Add the following variables for **Production** environment:

```bash
# Required Production Variables
NEXT_PUBLIC_API_URL=https://api.devskyy.app
NEXT_PUBLIC_SITE_URL=https://app.devskyy.app
BACKEND_URL=https://api.devskyy.app

# Feature Flags
NEXT_PUBLIC_ENABLE_3D_PIPELINE=true
NEXT_PUBLIC_ENABLE_ROUND_TABLE=true

# Stack Auth (optional - configure if using authentication)
NEXT_PUBLIC_STACK_PROJECT_ID=your-project-id
NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=pck_...
STACK_SECRET_SERVER_KEY=ssk_...
```

1. Click **Save** for each variable

---

## Step 2: Add Custom Domain in Vercel Dashboard

### Option A: Using Vercel Dashboard (Recommended)

1. In your Vercel project, go to **Settings → Domains**
2. Click **Add Domain**
3. Enter `app.devskyy.app`
4. Click **Add**

Vercel will provide DNS configuration instructions:

- **A Record**: `76.76.21.21` (Vercel's IP)
- **AAAA Record**: `2606:4700:4700::1111` (Vercel's IPv6)

### Option B: Using Vercel CLI

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login to Vercel
vercel login

# Add domain to project
vercel domains add app.devskyy.app
```

---

## Step 3: Configure DNS Records

Update your DNS provider (e.g., Cloudflare, Namecheap, GoDaddy) with the following records:

### A Record (IPv4)

```
Type: A
Name: app
Value: 76.76.21.21
TTL: Auto (or 3600)
```

### AAAA Record (IPv6) - Optional but Recommended

```
Type: AAAA
Name: app
Value: 2606:4700:4700::1111
TTL: Auto (or 3600)
```

### Alternative: CNAME Record (if subdomain)

If your DNS provider supports CNAME for apex domains:

```
Type: CNAME
Name: app
Value: cname.vercel-dns.com
TTL: Auto (or 3600)
```

**Note**: DNS propagation can take 5-60 minutes depending on your provider.

---

## Step 4: Verify Domain Configuration

### Using Vercel Dashboard

1. Go to **Settings → Domains**
2. Check the status of `app.devskyy.app`
3. Wait for the status to change to **Valid**
4. SSL certificate will be automatically issued (Let's Encrypt)

### Using Vercel CLI

```bash
# Check domain status
vercel domains ls

# Verify DNS configuration
vercel domains verify app.devskyy.app
```

### Using Command Line Tools

```bash
# Check A record
dig app.devskyy.app +short
# Expected: 76.76.21.21

# Check AAAA record
dig app.devskyy.app AAAA +short
# Expected: 2606:4700:4700::1111

# Check SSL certificate
curl -I https://app.devskyy.app
# Expected: HTTP/2 200 (after deployment)
```

---

## Step 5: Deploy to Production

### Option A: Git-based Deployment (Automatic)

1. Push changes to your main/production branch:

   ```bash
   git add .
   git commit -m "feat: configure app.devskyy.app domain"
   git push origin main
   ```

2. Vercel will automatically deploy to the custom domain

### Option B: Manual Deployment via CLI

```bash
# Deploy to production
vercel --prod

# Or deploy with environment
vercel deploy --prod
```

---

## Step 6: Verify Production Deployment

1. **Test the Domain**:

   ```bash
   curl -I https://app.devskyy.app
   ```

   Expected response: `HTTP/2 200` or `307` (redirect to `/dashboard`)

2. **Check Redirect**:

   ```bash
   curl -L https://app.devskyy.app/
   ```

   Should redirect to `https://app.devskyy.app/dashboard`

3. **Test API Proxy**:

   ```bash
   curl https://app.devskyy.app/api/health
   ```

   Should proxy to `https://api.devskyy.app/health`

4. **Browser Test**:
   - Visit `https://app.devskyy.app` in a browser
   - Should redirect to `https://app.devskyy.app/dashboard`
   - Check browser console for any errors
   - Verify SSL certificate (green padlock)

---

## Expected Behavior After Configuration

### URL Behavior

- `https://app.devskyy.app/` → Redirects to `https://app.devskyy.app/dashboard` (307)
- `https://app.devskyy.app/dashboard` → Loads Next.js dashboard
- `https://app.devskyy.app/api/*` → Proxies to `https://api.devskyy.app/*`

### SSL/TLS

- **Automatic SSL**: Vercel automatically provisions and renews Let's Encrypt certificates
- **HTTPS Only**: HTTP requests are automatically redirected to HTTPS
- **Certificate Renewal**: Automatic every 60 days

### Performance

- **Global CDN**: Content served from Vercel's global edge network
- **Auto-scaling**: Serverless functions scale automatically
- **Cold Start**: First request may take 2-3 seconds (Lambda cold start)

### Security Headers

The following headers are automatically added (via `vercel.json`):

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Access-Control-Allow-Origin: *` (for `/api/*` routes)

---

## Troubleshooting

### DNS Not Resolving

```bash
# Clear DNS cache (macOS)
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Clear DNS cache (Windows)
ipconfig /flushdns

# Clear DNS cache (Linux)
sudo systemd-resolve --flush-caches
```

### SSL Certificate Issues

- **Wait 5-10 minutes** after DNS propagation for Vercel to issue certificate
- Check **Settings → Domains** in Vercel dashboard for certificate status
- Ensure DNS records are correctly configured (A/AAAA or CNAME)

### API Proxy Not Working

1. Verify `BACKEND_URL` environment variable is set to `https://api.devskyy.app`
2. Check `vercel.json` rewrites configuration
3. Test backend directly: `curl https://api.devskyy.app/health`
4. Check Vercel deployment logs: `vercel logs --follow`

### Deployment Failures

```bash
# Check build logs
vercel logs --follow

# Check environment variables
vercel env ls

# Force redeploy
vercel --prod --force
```

---

## Additional Configuration

### Custom Error Pages

Create custom error pages in `frontend/app/`:

- `not-found.tsx` - 404 page
- `error.tsx` - 500 page

### Analytics

Enable Vercel Analytics:

1. Go to **Analytics** tab in Vercel dashboard
2. Click **Enable Analytics**
3. Add to `frontend/app/layout.tsx`:

   ```tsx
   import { Analytics } from '@vercel/analytics/react';

   export default function RootLayout({ children }) {
     return (
       <html>
         <body>
           {children}
           <Analytics />
         </body>
       </html>
     );
   }
   ```

### Monitoring

Enable Vercel Speed Insights:

```tsx
import { SpeedInsights } from '@vercel/speed-insights/next';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <SpeedInsights />
      </body>
    </html>
  );
}
```

---

## Production Checklist

- [ ] Environment variables configured in Vercel dashboard
- [ ] DNS A/AAAA records configured
- [ ] Domain added in Vercel (Settings → Domains)
- [ ] Domain status shows "Valid" in Vercel
- [ ] SSL certificate automatically issued
- [ ] `https://app.devskyy.app/` redirects to `/dashboard`
- [ ] API routes proxy to `https://api.devskyy.app`
- [ ] Browser console shows no errors
- [ ] SSL certificate verified (green padlock)
- [ ] Analytics enabled (optional)

---

## Support

- **Vercel Documentation**: <https://vercel.com/docs/projects/domains>
- **DNS Help**: <https://vercel.com/docs/projects/domains/troubleshooting>
- **DevSkyy Issues**: <https://github.com/damBruh/DevSkyy/issues>

---

## Related Files

- `/vercel.json` - Vercel deployment configuration
- `/frontend/.env.production` - Production environment variables
- `/frontend/next.config.js` - Next.js configuration with redirects and rewrites
- `/nginx-app.devskyy.app.conf` - Self-hosted Nginx alternative

---

**Last Updated**: 2026-01-08
