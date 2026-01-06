# AI Tools & HuggingFace Spaces Page

## Overview

This page provides an interactive interface for browsing and using 5 HuggingFace Spaces embedded via iframes.

## Features

### 1. Space Configuration (`/lib/hf-spaces.ts`)
- **Type-safe HFSpace interface**: Defines structure for each space
- **5 Pre-configured spaces**:
  - 3D Model Converter (conversion)
  - Flux Upscaler (generation)
  - LoRA Training Monitor (training)
  - Product Analyzer (analysis)
  - Product Photography (generation)
- **Helper functions**: Search, filter by category, get by ID

### 2. HFSpaceCard Component (`/components/HFSpaceCard.tsx`)
- **Iframe embedding** with security sandbox
- **Fullscreen mode** toggle
- **Refresh button** to reload iframe
- **External link** to open in new tab
- **Responsive design** with mobile support
- **Accessibility** with ARIA labels

### 3. AI Tools Page (`/app/ai-tools/page.tsx`)
- **Tab navigation** for quick space switching
- **Search functionality** across name, description, and tags
- **Category filters**: All, Generation, Analysis, Training, Conversion
- **Grid view** showing all spaces when not fullscreen
- **Active space** display with fullscreen option
- **Responsive layout** for mobile/desktop

## Usage

### Navigation
The page is accessible via:
- URL: `/ai-tools`
- Navigation menu: "AI Spaces"

### Features

#### Search
```typescript
// Search by name, description, or tags
searchQuery: "3D converter"
```

#### Category Filtering
- All Spaces
- Generation (2 spaces)
- Analysis (1 space)
- Training (1 space)
- Conversion (1 space)

#### Tab Navigation
Click any tab to switch to that space. Active tab is highlighted with brand color.

#### Fullscreen Mode
Click the fullscreen button to expand the iframe. Exit with the minimize button or same toggle.

#### External Links
Click the external link icon to open the space in a new tab on HuggingFace.

#### Refresh
Click refresh to reload the iframe content.

## Configuration

### Adding New Spaces

Edit `/lib/hf-spaces.ts`:

```typescript
{
  id: 'new-space',
  name: 'New Space Name',
  description: 'Description of the space',
  url: 'https://huggingface.co/spaces/skyyrose/new-space',
  icon: '🚀',
  category: 'generation', // or 'analysis', 'training', 'conversion'
  tags: ['tag1', 'tag2', 'tag3'],
}
```

### Security

Iframes use strict sandbox permissions:
- `allow-scripts` - Required for interactive apps
- `allow-same-origin` - Required for many HF Spaces
- `allow-forms` - For form submissions
- `allow-downloads` - For file downloads
- `allow-popups` - For modal dialogs
- `allow-modals` - For alert/confirm dialogs

Additional security:
- `rel="noopener noreferrer"` on external links
- Lazy loading for performance
- CSP-friendly implementation

## File Structure

```
frontend/
├── app/
│   └── ai-tools/
│       ├── page.tsx          # Main AI Tools page
│       └── README.md         # This file
├── components/
│   ├── HFSpaceCard.tsx       # Space card component
│   ├── Navigation.tsx        # Updated with AI Spaces link
│   └── index.ts              # Component exports
└── lib/
    └── hf-spaces.ts          # Space configuration
```

## Acceptance Criteria Status

- ✅ Tools page shows all 5 HF Spaces
- ✅ Tab navigation works
- ✅ Iframes load correctly
- ✅ Fullscreen mode functional
- ✅ External links work
- ✅ Responsive design (mobile/tablet/desktop)
- ✅ Search functionality
- ✅ Category filtering
- ✅ Refresh functionality
- ✅ Accessibility features

## Browser Compatibility

- Modern browsers with iframe support
- JavaScript required
- CSS Grid and Flexbox support
- Tailwind CSS 3.x

## Performance

- Lazy loading for iframes
- Optimized re-renders with React keys
- Efficient search/filter operations
- Responsive images and icons

## Future Enhancements

1. **Space favorites**: Save preferred spaces
2. **Usage analytics**: Track which spaces are most used
3. **Recent history**: Show recently accessed spaces
4. **Custom spaces**: Allow users to add their own HF Spaces
5. **Embedding options**: Control iframe size, refresh interval
6. **Error handling**: Better error states for failed iframe loads
7. **Performance metrics**: Monitor iframe load times
8. **Space ratings**: User ratings and reviews
