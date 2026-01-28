# Common Patterns

## API Response
```typescript
interface ApiResponse<T> {
  success: boolean; data?: T; error?: string
  meta?: { total: number; page: number; limit: number }
}
```

## Repository Pattern
```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

## Custom Hooks
```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}
```

## New Features
1. Search for battle-tested skeleton projects
2. Evaluate with parallel agents (security, extensibility)
3. Clone and iterate within proven structure
