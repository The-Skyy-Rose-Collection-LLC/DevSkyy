# DevSkyy Coding Standards

## CRITICAL RULES

### Always Use Actual Production-Ready Code

- NO placeholder code
- NO stub implementations
- NO half-baked solutions
- Every piece of code must be fully functional and tested
- Use real CDN URLs, real APIs, real implementations

### Three.js Integration

- Use ES Modules with proper import maps
- CDN: `https://cdn.jsdelivr.net/npm/three@0.160.0/`
- Always include proper module loading setup
- Test WebGL rendering before deploying

### WordPress Theme Development

- Validate PHP syntax before upload
- Proper child theme structure with Template header
- Correct script enqueuing with proper dependencies
- Use `type="module"` for ES modules

### Quality Standards

- Run linters before committing
- Test all functionality locally before deploying
- No "stored 0%" warnings should concern - that's normal for zip directories
- Deep test integrations between systems
