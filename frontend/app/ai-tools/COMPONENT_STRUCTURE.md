# AI Tools Component Structure

## Visual Hierarchy

```
AIToolsPage (/app/ai-tools/page.tsx)
│
├── Header Section
│   ├── Title: "AI Tools & Spaces"
│   ├── Icon: Sparkles
│   └── Description: "Explore and use 5 powerful AI tools..."
│
├── Search & Filter Controls
│   ├── Search Bar
│   │   ├── Search Icon
│   │   └── Input Field (search by name, description, tags)
│   │
│   └── Category Filters
│       ├── All Spaces Button
│       ├── Generation Button
│       ├── Analysis Button
│       ├── Training Button
│       └── Conversion Button
│
├── Tab Navigation
│   ├── 3D Model Converter Tab
│   ├── Flux Upscaler Tab
│   ├── LoRA Training Monitor Tab
│   ├── Product Analyzer Tab
│   └── Product Photography Tab
│
├── Active Space Display
│   └── HFSpaceCard Component
│       ├── Card Header
│       │   ├── Space Icon (emoji)
│       │   ├── Space Name
│       │   ├── Space Description
│       │   └── Control Buttons
│       │       ├── Refresh Button
│       │       ├── Fullscreen Toggle
│       │       └── External Link
│       │
│       └── Card Content
│           └── Iframe (HuggingFace Space)
│
└── Grid View (when not fullscreen)
    ├── Grid Header
    │   ├── Grid Icon
    │   ├── "All Spaces" Title
    │   └── Count Badge
    │
    └── Space Cards (Grid)
        ├── Card 1: 3D Converter
        ├── Card 2: Flux Upscaler
        ├── Card 3: LoRA Monitor
        ├── Card 4: Product Analyzer
        └── Card 5: Product Photography
```

## Component Breakdown

### 1. AIToolsPage (Main Container)
```typescript
Location: /frontend/app/ai-tools/page.tsx
Type: Client Component ('use client')
State:
  - selectedSpace: HFSpace
  - fullscreen: boolean
  - searchQuery: string
  - categoryFilter: string
```

### 2. HFSpaceCard (Reusable Component)
```typescript
Location: /frontend/components/HFSpaceCard.tsx
Props:
  - space: HFSpace
  - fullscreen?: boolean
  - onToggleFullscreen?: () => void
  - className?: string
State:
  - iframeKey: number (for refresh functionality)
```

### 3. UI Components (From /components/ui)
```typescript
- Card, CardHeader, CardTitle, CardContent
- Badge (for categories and counts)
- Button (not used, using native button for simplicity)
```

### 4. Icons (Lucide React)
```typescript
- Sparkles: Header icon
- Search: Search bar icon
- Grid: Grid view header icon
- Maximize2: Enter fullscreen icon
- Minimize2: Exit fullscreen icon
- ExternalLink: Open in new tab icon
- RefreshCw: Refresh iframe icon
```

## Data Flow

```
User Action
    ↓
State Update (useState)
    ↓
Component Re-render
    ↓
UI Update
```

### Examples:

**Search Flow:**
```
User types → searchQuery updated → filteredSpaces computed → Grid re-renders
```

**Tab Switch Flow:**
```
User clicks tab → selectedSpace updated → HFSpaceCard re-renders with new space
```

**Fullscreen Flow:**
```
User clicks fullscreen → fullscreen=true → Card styles change → Grid hides
```

**Refresh Flow:**
```
User clicks refresh → iframeKey incremented → iframe re-mounts → Space reloads
```

## CSS Classes Structure

### Responsive Breakpoints
```css
Mobile:  Base styles (< 640px)
Tablet:  lg: prefix (640px - 1024px)
Desktop: lg: and xl: prefixes (> 1024px)
```

### Key Tailwind Classes

**Container:**
```css
container mx-auto p-4 lg:p-6 space-y-6
```

**Header:**
```css
text-3xl lg:text-4xl font-bold flex items-center gap-3
```

**Search Bar:**
```css
w-full pl-10 pr-4 py-3 rounded-lg border focus:ring-2 focus:ring-brand-primary
```

**Category Buttons:**
```css
px-4 py-2 rounded-lg whitespace-nowrap font-medium transition-all
Active: bg-brand-primary text-white shadow-md
Inactive: bg-gray-100 dark:bg-gray-800 hover:bg-gray-200
```

**Tabs:**
```css
px-4 py-3 rounded-t-lg border-b-2
Active: border-brand-primary text-brand-primary
Inactive: border-transparent hover:bg-gray-100
```

**Grid:**
```css
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4
```

**Fullscreen Mode:**
```css
fixed inset-4 z-50 shadow-2xl
```

**Iframe:**
```css
w-full h-full border-0
Normal: h-[600px] lg:h-[700px]
Fullscreen: h-[calc(100vh-10rem)]
```

## State Management

### Local State (useState)
```typescript
// Selected space
const [selectedSpace, setSelectedSpace] = useState<HFSpace>(HF_SPACES[0]);

// Fullscreen mode
const [fullscreen, setFullscreen] = useState(false);

// Search query
const [searchQuery, setSearchQuery] = useState('');

// Category filter
const [categoryFilter, setCategoryFilter] = useState('all');

// Iframe refresh key (in HFSpaceCard)
const [iframeKey, setIframeKey] = useState(0);
```

### Derived State (Computed)
```typescript
// Filtered spaces based on search and category
const filteredSpaces = searchQuery
  ? searchSpaces(searchQuery)
  : getSpacesByCategory(categoryFilter);

// Ensure selected space is visible
const visibleSelectedSpace = filteredSpaces.find(
  (space) => space.id === selectedSpace.id
);
const displaySpace = visibleSelectedSpace || filteredSpaces[0] || HF_SPACES[0];
```

## Event Handlers

### User Interactions
```typescript
// Search input
onChange={(e) => setSearchQuery(e.target.value)}

// Category filter
onClick={() => {
  setCategoryFilter(cat.id);
  setSearchQuery('');
}}

// Tab selection
onClick={() => setSelectedSpace(space)}

// Fullscreen toggle
onClick={() => setFullscreen(!fullscreen)}

// Refresh iframe
onClick={() => setIframeKey(prev => prev + 1)}

// Grid card click
onClick={() => setSelectedSpace(space)}
```

## Conditional Rendering

### Search Results
```typescript
{filteredSpaces.length === 0 && (
  <Card>No spaces found</Card>
)}
```

### Grid View
```typescript
{!fullscreen && (
  <div className="grid">
    {/* Grid items */}
  </div>
)}
```

### Fullscreen Button
```typescript
{onToggleFullscreen && (
  <button onClick={onToggleFullscreen}>
    {fullscreen ? <Minimize2 /> : <Maximize2 />}
  </button>
)}
```

## Accessibility Features

### ARIA Labels
```typescript
aria-label={space.name}           // Icon
aria-label="Refresh iframe"       // Refresh button
aria-label="Enter fullscreen"     // Fullscreen button
aria-label="Open in new tab"      // External link
title={space.name}                // Iframe title
```

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Space to toggle checkboxes
- Arrow keys in grid navigation

### Screen Reader Support
- Semantic HTML (nav, main, section)
- Descriptive alt text
- ARIA landmarks
- Focus management

## Performance Optimizations

### React Optimizations
```typescript
// Key prop for efficient re-renders
key={iframeKey}
key={space.id}

// Conditional rendering to avoid unnecessary DOM
{!fullscreen && <GridView />}
```

### Lazy Loading
```typescript
// Iframe lazy loading
loading="lazy"
```

### Efficient Filtering
```typescript
// Single pass filter operations
const filteredSpaces = searchQuery
  ? searchSpaces(searchQuery)
  : getSpacesByCategory(categoryFilter);
```

## Security Considerations

### Iframe Sandbox
```typescript
sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups allow-modals"
allow="accelerometer; camera; microphone; clipboard-write"
```

### External Links
```typescript
target="_blank"
rel="noopener noreferrer"
```

### URL Validation
```typescript
// All URLs validated to be HuggingFace spaces
url: 'https://huggingface.co/spaces/skyyrose/...'
```

## File Dependencies

```
ai-tools/page.tsx
├── react (useState)
├── lucide-react (Icons)
├── @/components/HFSpaceCard
├── @/components/ui (Card, Badge)
└── @/lib/hf-spaces
    ├── HF_SPACES
    ├── SPACE_CATEGORIES
    ├── getSpacesByCategory
    ├── searchSpaces
    └── HFSpace (type)

HFSpaceCard.tsx
├── react (useState)
├── lucide-react (Icons)
├── @/components/ui (Card, CardHeader, CardTitle, CardContent)
└── @/lib/hf-spaces (HFSpace type)

hf-spaces.ts
└── (No dependencies - pure TypeScript)
```

## Testing Strategy

### Unit Tests
- Configuration validation
- Helper function logic
- Search/filter operations

### Component Tests
- HFSpaceCard rendering
- User interactions (click, type)
- State updates

### Integration Tests
- Full page flow
- Navigation between spaces
- Fullscreen mode

### E2E Tests (Future)
- Complete user journey
- Iframe loading
- External link navigation

---

**This structure provides a clear understanding of how all components work together to create the AI Tools page.**
