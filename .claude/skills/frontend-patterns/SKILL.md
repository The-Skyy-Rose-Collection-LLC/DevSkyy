---
name: frontend-patterns
description: React, Next.js, state management, and performance patterns.
---

# Frontend Development Patterns

## Component Patterns
- **Composition**: Card + CardHeader + CardBody
- **Compound**: Tabs context with Tab children
- **Render Props**: DataLoader with children function

## Custom Hooks
```typescript
// Debounce
const debounced = useDebounce(value, 500)

// Toggle
const [isOpen, toggle] = useToggle()

// Async data
const { data, loading } = useQuery('key', fetcher)
```

## Performance
- `React.memo()` for pure components
- `useMemo` for expensive computations
- `useCallback` for stable function refs
- `React.lazy()` for code splitting
- Virtual lists for large datasets

## State Management
- `useState` for local state
- `useReducer` for complex state
- Context + Reducer for global state

## Accessibility
- Semantic HTML elements
- ARIA labels on interactive elements
- Keyboard navigation support

## Related Tools
- **Skill**: `react-best-practices` for patterns
- **Skill**: `coding-standards` for TypeScript
- **Agent**: `code-reviewer` after writing components
