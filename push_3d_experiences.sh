#!/bin/bash
# =====================================================
# SKYYROSE 3D VIRTUAL EXPERIENCES - GIT PUSH SCRIPT
# =====================================================
# Run this script from your DevSkyy repo root directory
# 
# Usage: ./push_3d_experiences.sh
# =====================================================

set -e

echo "🌹 SkyyRose 3D Virtual Experiences - Push Script"
echo "================================================="

# Check we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository. Please run from DevSkyy root."
    exit 1
fi

# Check for changes
echo "📋 Checking for changes..."
git status

# Stage all HTML files
echo ""
echo "📁 Staging 3D experience files..."
git add skyyrose-black-rose-garden-complete.html 2>/dev/null || true
git add skyyrose-love-hurts-castle-complete.html 2>/dev/null || true
git add skyyrose-signature-runway-complete.html 2>/dev/null || true
git add skyyrose-black-rose-garden-production.html 2>/dev/null || true
git add skyyrose-love-hurts-castle-production.html 2>/dev/null || true
git add skyyrose-signature-runway-production.html 2>/dev/null || true

# Show staged files
echo ""
echo "✅ Staged files:"
git diff --cached --name-only

# Commit
echo ""
echo "💾 Creating commit..."
git commit -m "feat(3d): Complete SkyyRose 3D Virtual Experiences with verified assets

🌹 BLACK ROSE GARDEN - Gothic dark elegance theme
   - DamagedHelmet, GlassVaseFlowers, GlamVelvetSofa, IridescenceLamp, Corset GLB models
   - Poly Haven cobblestone_street_night_1k.hdr environment
   - 50 rose bushes, 800 petal particles, bloom effects

💜 LOVE HURTS CASTLE - Beauty and the Beast ballroom
   - 8 verified GLB models including ChairDamaskPurplegold
   - Poly Haven brown_photostudio_02_1k.hdr environment
   - 64-crystal chandelier, 10 pillars, 1200 magic particles

✨ SIGNATURE RUNWAY - Fashion show experience
   - 8 verified GLB models including MaterialsVariantsShoe, ChronographWatch
   - Poly Haven studio_small_09_1k.hdr environment
   - 80m runway, 10 animated spotlights, runway walk mode

All assets verified HTTP 200 from:
- KhronosGroup glTF-Sample-Assets (GitHub)
- Poly Haven HDRIs (CC0 License)

Three.js v0.160.0 with GLTFLoader, RGBELoader, OrbitControls, UnrealBloomPass"

# Push
echo ""
echo "🚀 Pushing to origin..."
git push origin main

echo ""
echo "✅ Done! Files pushed to GitHub."
echo "================================================="
