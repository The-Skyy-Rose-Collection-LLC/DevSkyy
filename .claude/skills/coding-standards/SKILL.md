---
name: coding-standards
description: Universal coding standards for TypeScript, JavaScript, React, Node.js.
---

# Coding Standards

## Core Principles
- **KISS**: Simplest solution that works
- **DRY**: Extract common logic
- **YAGNI**: Don't build before needed
- **Immutability**: Always `{...obj}`, never mutate

## TypeScript Rules
```typescript
// ✅ GOOD: Typed, descriptive, immutable
const updatedUser = { ...user, name: 'New' }

// ❌ BAD: any, mutation, unclear names
user.name = 'New'  // MUTATION!
```

## React Best Practices
- Functional components with typed props
- Custom hooks for reusable logic
- Functional state updates: `setCount(prev => prev + 1)`

## API Response Format
```typescript
interface ApiResponse<T> {
  success: boolean; data?: T; error?: string
}
```

## Code Smells
- Functions >50 lines → split
- Nesting >4 levels → early returns
- Magic numbers → named constants

## Related Tools
- **Agent**: `code-reviewer` after writing code
- **Agent**: `tdd-guide` for new features
- **Command**: `/verify` before commits
