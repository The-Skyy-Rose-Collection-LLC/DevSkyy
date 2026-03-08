# DevSkyy Dashboard — Developer Setup

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 22.x+ | [nodejs.org](https://nodejs.org) |
| npm | 10.x+ | Bundled with Node.js |
| Git | 2.x+ | `brew install git` |

**Do NOT use pnpm** — Vercel deployment breaks with pnpm on Node 22+. npm is the canonical package manager.

---

## 1. Clone & Install

```bash
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy/frontend
npm install
```

## 2. Environment Variables

Copy the example env file:

```bash
cp .env.example .env.local
```

Then fill in your values:

```env
# API Connection (required)
NEXT_PUBLIC_API_URL=http://localhost:8000    # Backend FastAPI server
NEXT_PUBLIC_WS_URL=ws://localhost:8000      # WebSocket endpoint
NEXT_PUBLIC_SITE_URL=http://localhost:3000   # This frontend

# Authentication (required)
NEXTAUTH_SECRET=<generate-with: openssl rand -base64 32>
NEXTAUTH_URL=http://localhost:3000

# WordPress Integration (optional for dashboard dev)
WORDPRESS_URL=https://skyyrose.co
WOOCOMMERCE_KEY=ck_your_consumer_key_here
WOOCOMMERCE_SECRET=cs_your_consumer_secret_here
NEXT_PUBLIC_WORDPRESS_URL=https://skyyrose.co

# Feature Flags
NEXT_PUBLIC_SITE_NAME=SkyyRose
NEXT_PUBLIC_ENABLE_ROUND_TABLE=true
```

### Pull env from Vercel (team members only)

```bash
npm run vercel:env:pull
```

## 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

- **Homepage**: `/`
- **Admin Dashboard**: `/admin` (requires login)
- **Login**: `/login`

## 4. Backend Connection

The dashboard authenticates against a FastAPI backend at `NEXT_PUBLIC_API_URL`. To work on dashboard UI without the backend:

1. The admin pages will load with empty/error states
2. Mock data can be added in the `lib/api/endpoints/` modules
3. The WordPress admin page (`/admin/wordpress`) proxies through Next.js API routes — it needs `WORDPRESS_URL` + WooCommerce keys

To run the full backend:

```bash
cd /path/to/DevSkyy
python3 -m uvicorn main_enterprise:app --reload --port 8000
```

## 5. Useful Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run lint` | Run Next.js linter |
| `npm run test:e2e` | Run Playwright E2E tests |
| `npm run deploy` | Deploy to Vercel preview |
| `npm run deploy:prod` | Deploy to Vercel production |

## 6. Project URLs

| Environment | URL |
|-------------|-----|
| Production | https://devskyy.app |
| Preview | Auto-generated per branch |
| WordPress | https://skyyrose.co |
| API (prod) | https://api.devskyy.app |

## 7. Troubleshooting

**`NEXTAUTH_SECRET` not set**: Generate one with `openssl rand -base64 32` and add to `.env.local`.

**Turbopack errors**: The `turbopack.root` is set to `..` (monorepo root). If you see resolution errors, ensure you're running from the `frontend/` directory.

**Image optimization fails**: Remote images must come from `*.skyyrose.co` or `*.devskyy.app` — configured in `next.config.ts`.

**API timeouts**: Default timeout is 30 seconds (`lib/api/client.ts`). File uploads get 120 seconds.
