# Coding Style

## Immutability (CRITICAL)
ALWAYS create new objects, NEVER mutate:
```javascript
// WRONG               // CORRECT
user.name = name       return { ...user, name }
```

## File Organization
- 200-400 lines typical, 800 max
- High cohesion, low coupling
- Organize by feature/domain

## Error Handling
```typescript
try {
  return await riskyOperation()
} catch (error) {
  throw new Error('User-friendly message', { cause: error })
}
```

## Input Validation
Use Zod at system boundaries:
```typescript
const schema = z.object({ email: z.string().email() })
```

## Quality Checklist
- [ ] Functions <50 lines, files <800 lines
- [ ] No deep nesting (>4 levels)
- [ ] No console.log or hardcoded values
- [ ] Immutable patterns used
