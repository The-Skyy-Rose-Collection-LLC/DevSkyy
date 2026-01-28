# Vercel Deployment

This skill provides comprehensive knowledge for deploying applications to Vercel. It activates when users mention "deploy to vercel", "vercel deployment", "vercel CLI", "vercel project setup", "vercel domains", "vercel edge functions", or encounter Vercel-related errors.

---

## Core Deployment Commands

### Initial Setup
```bash
# Install Vercel CLI globally
npm i -g vercel

# Login to Vercel
vercel login

# Link existing project
vercel link

# Initialize new project
vercel init
```

### Deployment Commands
```bash
# Deploy to preview (default)
vercel

# Deploy to production
vercel --prod

# Deploy with specific environment
vercel --env production

# Deploy and skip build
vercel --prebuilt

# Force new deployment
vercel --force
```

## Project Configuration

### vercel.json Structure
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url"
  },
  "build": {
    "env": {
      "NODE_ENV": "production"
    }
  }
}
```

### Environment Variables
```bash
# Add environment variable
vercel env add VARIABLE_NAME

# Pull environment variables locally
vercel env pull .env.local

# List all environment variables
vercel env ls

# Remove environment variable
vercel env rm VARIABLE_NAME
```

## Domain Configuration

```bash
# Add custom domain
vercel domains add example.com

# List domains
vercel domains ls

# Configure DNS
vercel dns add example.com @ A 76.76.21.21

# Remove domain
vercel domains rm example.com
```

## Common Errors and Solutions

### Build Failures

**Error: "Build failed"**
- Check `vercel.json` buildCommand matches package.json scripts
- Verify all dependencies are in package.json (not just devDependencies for production builds)
- Check Node.js version compatibility in package.json engines field

**Error: "Function size too large"**
- Enable output file tracing in next.config.js
- Use dynamic imports to split code
- Check for accidentally bundled large dependencies

### Deployment Failures

**Error: "Deployment timed out"**
- Check for infinite loops in build process
- Verify API routes don't have blocking operations
- Increase function timeout in vercel.json

**Error: "Rate limit exceeded"**
- Wait and retry deployment
- Use `vercel --force` only when necessary
- Consider upgrading Vercel plan for higher limits

## Edge Functions

```javascript
// middleware.ts for edge runtime
export const config = {
  matcher: '/api/:path*',
}

export function middleware(request) {
  // Edge function logic
  return NextResponse.next()
}
```

## Autonomous Recovery Steps

When encountering errors:

1. **Capture the exact error message**
2. **Use Context7 to fetch latest Vercel documentation** with query like "vercel [error type] solution"
3. **Check vercel.json configuration** against documentation
4. **Verify environment variables** are set correctly
5. **Check build logs** with `vercel logs [deployment-url]`
6. **Apply fix and redeploy** with `vercel --prod`
7. **Validate deployment** by checking the deployment URL

## Integration with Next.js

For Next.js projects:
- Vercel auto-detects Next.js and applies optimal settings
- Use `next.config.js` for framework-specific configuration
- Edge runtime supported for middleware and API routes
- ISR (Incremental Static Regeneration) fully supported

## Useful CLI Commands

```bash
# View deployment logs
vercel logs [deployment-url]

# List all deployments
vercel ls

# Rollback to previous deployment
vercel rollback

# Inspect deployment
vercel inspect [deployment-url]

# View project info
vercel project ls
```
