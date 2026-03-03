# Admin Dashboard

> 19 admin sections | Next.js App Router | `/admin/*` routes

---

## Structure

```
admin/
├── layout.tsx                 # Admin layout wrapper
├── page.tsx                   # Dashboard overview (/admin)
│
├── agents/                    # Agent management + monitoring
├── autonomous/                # Autonomous agent controls
├── round-table/               # Multi-LLM consensus interface
├── monitoring/                # System health + metrics
├── jobs/                      # Background job tracking
├── tasks/                     # Task queue management
│
├── assets/                    # Asset management
├── imagery/                   # Image pipeline controls
├── 3d-pipeline/               # 3D generation pipeline
├── mascot/                    # Mascot asset management
│
├── conversion/                # Conversion analytics
├── journey-analytics/         # User journey tracking
├── social-media/              # Social media integration
│
├── pipeline/                  # ML pipeline management
├── huggingface/               # HF Spaces + models
├── qa/                        # Quality assurance tools
│
├── wordpress/                 # WordPress sync controls
├── vercel/                    # Deployment management
└── settings/                  # Admin settings
```

---

## Patterns

- Each subdirectory is an App Router route segment with its own `page.tsx`
- `layout.tsx` provides the admin shell (sidebar nav, auth gate)
- API calls go through `/api/monitoring/*` routes (health, metrics)

---

## Verification

```bash
# List all admin routes
ls frontend/app/admin/*/page.tsx 2>/dev/null | wc -l
```
