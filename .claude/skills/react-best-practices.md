---
name: react-best-practices
description: React/TypeScript hooks, performance, accessibility patterns.
---

# React Best Practices

## Hooks Rules
- `useState` for local state
- `useEffect` with proper cleanup
- `useMemo` for expensive computations
- `useCallback` for stable function references
- `useRef` for mutable refs without re-render

## Performance
```typescript
// Memoize expensive operations
const sorted = useMemo(() => items.sort(...), [items])

// Stable callbacks
const handleClick = useCallback(() => {...}, [deps])

// Pure components
export const Card = React.memo(({ data }) => {...})
```

## TypeScript
```typescript
interface Props { name: string; onClick: () => void }
// Avoid: any, non-null assertions (!.)
```

## Accessibility
- Semantic HTML: `<header>`, `<main>`, `<nav>`
- ARIA labels on buttons/inputs
- Keyboard navigation support

## Error Handling
```typescript
<ErrorBoundary fallback={<Error />}>
  <Component />
</ErrorBoundary>
```

## Related Tools
- **Skill**: `frontend-patterns` for components
- **Skill**: `coding-standards` for TypeScript
- **Agent**: `code-reviewer` for review
- **Agent**: `tdd-guide` for component tests
