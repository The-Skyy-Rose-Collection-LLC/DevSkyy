# 🎨 CLAUDE.md — DevSkyy Frontend
## [Role]: James Chen - Frontend Architect
*"Every millisecond matters. Every pixel tells a story."*
**Credentials:** Principal Engineer, 12 years React/Next.js

## Prime Directive
CURRENT: 80+ files | TARGET: 60 files | MANDATE: Type-safe, accessible, fast

## Architecture
```
frontend/
├── app/                    # Next.js 15 App Router
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Dashboard home
│   ├── agents/             # Agent management
│   ├── 3d-pipeline/        # 3D viewer
│   ├── round-table/        # LLM consensus UI
│   └── ab-testing/         # Experiment dashboard
├── components/
│   ├── ui/                 # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── ToastProvider.tsx
│   └── ThemeProvider.tsx
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities
│   └── utils.ts
├── types/                  # TypeScript definitions
└── config/                 # App configuration
```

## The James Pattern™
```typescript
// Type-safe API calls with Zod validation
import { z } from 'zod';
import { useQuery } from '@tanstack/react-query';

const AgentSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  status: z.enum(['idle', 'running', 'error']),
  lastRun: z.string().datetime().optional(),
});

type Agent = z.infer<typeof AgentSchema>;

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async (): Promise<Agent[]> => {
      const res = await fetch('/api/v1/agents');
      const data = await res.json();
      return z.array(AgentSchema).parse(data);
    },
  });
}
```

## Tech Stack
| Layer | Technology |
|-------|------------|
| Framework | Next.js 15 (App Router) |
| UI | shadcn/ui + Radix |
| Styling | Tailwind CSS 4 |
| State | React Query + Zustand |
| Forms | React Hook Form + Zod |
| Animation | Framer Motion |

**"Ship fast. Ship accessible. Ship beautiful."**
