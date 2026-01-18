---
name: react-best-practices
description: React/TypeScript best practices - hooks, performance, accessibility, patterns
tags: [react, typescript, frontend, accessibility, performance]
---

# React Best Practices Skill

Apply React and TypeScript best practices to frontend code, ensuring performance, accessibility, and maintainability.

## 🎯 Core Principles

```
Hooks → Performance → Accessibility → Testing → Error Handling → Types
```

---

## Phase 1: Component Structure Analysis 🏗️

### 1.1: Check for Class Components (Should Use Functional)

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "extends (React\\.)?Component|extends (React\\.)?PureComponent",
  "path": "src",
  "glob": "*.{tsx,jsx}",
  "output_mode": "content"
}
</params>
</tool_call>

### 1.2: Check for Proper Hook Usage

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "useState|useEffect|useMemo|useCallback|useRef|useContext",
  "path": "src",
  "glob": "*.{tsx,jsx}",
  "output_mode": "files_with_matches"
}
</params>
</tool_call>

---

## Phase 2: Performance Patterns ⚡

### 2.1: Missing useMemo/useCallback for Expensive Operations

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "\\.map\\(|\\.(filter|reduce|sort|find)\\(",
  "path": "src/components",
  "glob": "*.{tsx,jsx}",
  "output_mode": "content"
}
</params>
</tool_call>

### 2.2: Check for Proper Dependency Arrays

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "use(Effect|Callback|Memo)\\([^)]+,\\s*\\[\\]\\)",
  "path": "src",
  "glob": "*.{tsx,jsx}",
  "output_mode": "content"
}
</params>
</tool_call>

### 2.3: Detect Missing React.memo for Pure Components

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "export (default )?(const|function) \\w+.*=>|export (default )?function \\w+",
  "path": "src/components",
  "glob": "*.{tsx,jsx}",
  "output_mode": "files_with_matches"
}
</params>
</tool_call>

---

## Phase 3: TypeScript Best Practices 📐

### 3.1: Check for 'any' Types

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": ": any[^a-zA-Z]|<any>|as any",
  "path": "src",
  "glob": "*.{ts,tsx}",
  "output_mode": "content"
}
</params>
</tool_call>

### 3.2: Check for Proper Props Interface Definitions

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "interface \\w+Props|type \\w+Props",
  "path": "src/components",
  "glob": "*.tsx",
  "output_mode": "files_with_matches"
}
</params>
</tool_call>

### 3.3: Check for Non-null Assertions (Should Minimize)

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "!\\.",
  "path": "src",
  "glob": "*.{ts,tsx}",
  "output_mode": "content"
}
</params>
</tool_call>

---

## Phase 4: Accessibility (a11y) ♿

### 4.1: Check for Missing ARIA Labels

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "<(button|a|input|img)[^>]*(?<!aria-label)[^>]*>",
  "path": "src",
  "glob": "*.tsx",
  "output_mode": "content"
}
</params>
</tool_call>

### 4.2: Check for Semantic HTML Elements

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "<(header|main|footer|nav|section|article|aside)>",
  "path": "src",
  "glob": "*.tsx",
  "output_mode": "files_with_matches"
}
</params>
</tool_call>

### 4.3: Check for Role Attributes

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "role=",
  "path": "src",
  "glob": "*.tsx",
  "output_mode": "content"
}
</params>
</tool_call>

---

## Phase 5: Error Handling 🛡️

### 5.1: Check for Error Boundaries

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "ErrorBoundary|componentDidCatch|getDerivedStateFromError",
  "path": "src",
  "glob": "*.{tsx,ts}",
  "output_mode": "content"
}
</params>
</tool_call>

### 5.2: Check for Try-Catch in Async Operations

<tool_call>
<tool>Grep</tool>
<params>
{
  "pattern": "async.*\\{[^}]*try[^}]*catch|fetch\\(.*\\.catch",
  "path": "src",
  "glob": "*.{tsx,ts}",
  "multiline": true,
  "output_mode": "content"
}
</params>
</tool_call>

---

## Phase 6: Testing Coverage 🧪

### 6.1: Check for Component Tests

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "find src -name '*.tsx' | xargs -I{} bash -c 'basename \"{}\" | sed \"s/.tsx//\"' | while read comp; do if ! find src -name \"${comp}.test.tsx\" -o -name \"${comp}.spec.tsx\" | grep -q .; then echo \"Missing test: $comp\"; fi; done | head -20",
  "description": "Find components without tests",
  "timeout": 30000
}
</params>
</tool_call>

### 6.2: Run Jest with Coverage

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pnpm test:coverage --collectCoverageFrom='src/**/*.{ts,tsx}' --coverageReporters='text-summary' 2>&1 | tail -20 || echo 'No test:coverage script'",
  "description": "Run test coverage",
  "timeout": 120000
}
</params>
</tool_call>

---

## Best Practices Checklist ✅

### Hooks Rules
- [ ] `useState` for local state
- [ ] `useReducer` for complex state
- [ ] `useEffect` with proper cleanup
- [ ] `useMemo` for expensive computations
- [ ] `useCallback` for stable function references
- [ ] `useRef` for mutable refs without re-render

### Performance
- [ ] `React.memo()` for pure components
- [ ] Virtual list for large lists (`react-virtualized`)
- [ ] Code splitting with `React.lazy()`
- [ ] Avoid inline object/function props

### TypeScript
- [ ] Define props interfaces
- [ ] Avoid `any` types
- [ ] Use generics for reusable components
- [ ] Discriminated unions for state

### Accessibility
- [ ] Semantic HTML elements
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation support
- [ ] Color contrast compliance

---

## Quick Fixes 🔧

### Add React.memo to Component

```tsx
// Before
export const MyComponent = ({ data }: Props) => { ... };

// After
export const MyComponent = React.memo(({ data }: Props) => { ... });
```

### Add Proper useCallback

```tsx
// Before
const handleClick = () => doSomething(id);

// After
const handleClick = useCallback(() => doSomething(id), [id]);
```

### Add Error Boundary

```tsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary fallback={<ErrorFallback />}>
  <MyComponent />
</ErrorBoundary>
```
