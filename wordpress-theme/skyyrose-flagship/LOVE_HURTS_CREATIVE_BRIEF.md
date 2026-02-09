# Love Hurts Collection - Creative Direction

## Inspiration: Beauty and the Beast - Enchanted Rose

### Core Aesthetic
**"The Enchanted Ballroom of the Cursed Rose"**

This experience should transport users into a **Beauty and the Beast**-inspired gothic romance, centered around the iconic enchanted rose under glass. The atmosphere should blend **dark elegance** with **magical enchantment**.

---

## Scene Elements

### 1. **The Enchanted Rose (Centerpiece)**
- **Glass dome** with glowing rose inside
- Rose petals slowly falling and dissolving into sparkles
- Pulsing golden/red glow emanating from the rose
- Rose loses petals over time (subtle animation)
- Glass dome has magical shimmer/reflection
- **Particle effects**: Floating rose petals, golden sparkles

### 2. **The Grand Ballroom**
- **Baroque/Rococo architecture**:
  - Ornate columns with gold leaf accents
  - Vaulted ceiling with frescoes
  - Crystal chandeliers with candle lights
  - Grand arched windows
  - Marble floors with reflections

- **Candlelit Ambiance**:
  - Hundreds of floating candles (like Hogwarts)
  - Flickering warm golden light
  - Dramatic shadows on walls
  - Candlelight reflects off surfaces

### 3. **Stained Glass Windows**
- **Large gothic windows** depicting rose motifs
- Colored light streaming through (purples, reds, golds)
- Moonlight filtering through from behind
- Window shadows cast on floor

### 4. **Magical Elements**
- **Floating magical particles** (golden dust, sparkles)
- **Enchanted book** on podium (Beauty's favorite)
- **Mirror** on wall (magic mirror Easter egg)
- **Animated suits of armor** (subtle movements)
- **Floating candelabras** (Lumière reference)
- **Enchanted wardrobe** doors slightly ajar
- **Teapot and teacup** on table (Mrs. Potts reference)

### 5. **Product Display Integration**
- Products displayed on:
  - Ornate golden pedestals
  - Mannequins in alcoves
  - Floating display cases with magical glow
  - Rose-themed stands
- Each product hotspot has rose petal particles
- Click reveals product in enchanted mirror reflection

---

## Color Palette

**Primary:**
- Deep crimson red (#8B0000)
- Royal gold (#FFD700)
- Rich purple (#4B0082)
- Midnight blue (#191970)

**Accents:**
- Warm candlelight amber (#FFBF00)
- Rose pink (#FF69B4)
- Antique gold (#C5B358)
- Shadow black (#0A0A0A)

**Magical Effects:**
- Ethereal white/gold glow
- Rose petal red with shimmer
- Purple magical mist

---

## Lighting Design

1. **Primary Light Sources**:
   - Chandelier (warm golden downlight)
   - Candles (flickering point lights)
   - Enchanted rose glow (pulsing red/gold)
   - Moonlight through windows (cool blue)
   - Stained glass colored light

2. **Atmosphere**:
   - Volumetric fog/mist
   - God rays through windows
   - Candlelight bloom effect
   - Soft shadows for romance
   - Magical shimmer particles

3. **Three.js Implementation**:
   - Multiple `PointLight` sources (candles)
   - `DirectionalLight` (moonlight)
   - `SpotLight` on enchanted rose
   - `HemisphereLight` for ambient
   - Post-processing: Bloom, God Rays, Vignette

---

## Audio Design

**Background Music:**
- Orchestral waltz (Beauty and the Beast theme inspiration)
- Soft string quartet
- Magical chime sounds

**Ambient Sounds:**
- Crackling candle flames
- Soft magical sparkle sounds
- Distant thunder (for drama)
- Clock ticking (Beast's curse)
- Gentle wind through windows

**Interactive Sounds:**
- Rose petal falling (soft whoosh)
- Product hotspot hover (magical chime)
- Click sound (enchanted activation)
- Portal open (mystical whoosh)

---

## Interactive Features

### Navigation
1. **Room Sections**:
   - Main Ballroom (dance floor)
   - Rose Alcove (centerpiece close-up)
   - Product Gallery (side alcoves)
   - Mirror Chamber (magic mirror interaction)
   - Library Corner (Beast's library)

2. **Camera Transitions**:
   - Smooth cinematic movements
   - Orbit around enchanted rose
   - Fly-through ballroom
   - Zoom to product displays

### Product Hotspots
- Glowing rose-shaped markers
- Pulsing golden rings
- Hover: Rose petals swirl around product
- Click: Magical portal opens to product detail
- Each product has enchanted backstory text

### Special Interactions
- Click enchanted rose → Special collection reveal
- Click mirror → See yourself with products (AR try-on)
- Click chandelier → Lights dim/brighten
- Click windows → Day/night cycle
- Easter eggs: Find all Beauty & Beast references

---

## Technical Requirements

### Three.js Scene
```javascript
// Key Components:
- OrbitControls for camera navigation
- GLTFLoader for 3D models (rose, ballroom)
- Particle systems (rose petals, sparkles)
- Bloom post-processing
- God rays shader
- Reflection/refraction materials
- Dynamic lighting system
- Audio manager for music/SFX
```

### Performance Optimization
- LOD for ballroom architecture
- Texture atlasing for efficiency
- Particle count limits based on device
- Mobile: Reduce particle effects
- Progressive asset loading
- Fallback for older devices

### Assets Needed
- 3D model: Grand ballroom architecture
- 3D model: Enchanted rose under glass
- 3D model: Chandelier (crystal)
- 3D model: Suits of armor
- 3D model: Product pedestals
- Textures: Marble, gold, glass, fabric
- HDR environment map: Ballroom lighting
- Audio: Waltz music, ambient sounds

---

## User Experience Flow

1. **Entry**: Camera starts outside ballroom doors
2. **Reveal**: Doors magically open, rose glow visible
3. **Welcome**: Float into ballroom, chandelier lights ignite
4. **Exploration**: User can navigate room sections
5. **Discovery**: Find product hotspots and Easter eggs
6. **Interaction**: Click products to view in mirror
7. **Purchase**: Add to cart from within experience

---

## Inspiration References

**Visual:**
- Disney's Beauty and the Beast (1991 & 2017)
- Versailles Hall of Mirrors
- Gothic cathedrals (Notre-Dame)
- Baroque palaces
- The Phantom of the Opera aesthetics

**Interactive:**
- Drake-related.com room navigation
- Museum of Other Realities (VR)
- Immersive Van Gogh experiences

**Technical:**
- Three.js realistic lighting demos
- WebGL particle systems
- Procedural animation examples

---

## Success Criteria

✅ User feels transported to enchanted ballroom
✅ Rose centerpiece is mesmerizing and magical
✅ Candlelight creates romantic atmosphere
✅ Products integrate naturally into scene
✅ Smooth 60fps performance on desktop
✅ 30fps acceptable on mobile
✅ Accessible navigation and controls
✅ Memorable, shareable experience

---

**This is a FLAGSHIP experience - make it ICONIC!**
