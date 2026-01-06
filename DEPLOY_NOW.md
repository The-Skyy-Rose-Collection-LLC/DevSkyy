# 🚀 Deploy DevSkyy to Vercel - Quick Reference Card

**Status**: ✅ Ready to Deploy | **Time**: 10 minutes

---

## 📋 Pre-Flight Checklist

- [x] HuggingFace Spaces configured (5 spaces)
- [x] Navigation updated (AI Spaces link)
- [x] Vercel project linked
- [x] Documentation created
- [ ] Environment variables set
- [ ] Deployment triggered
- [ ] Verification completed

---

## ⚡ Quick Deploy (3 Steps)

### Step 1: Set Environment Variables (2 min)

Go to: https://vercel.com/dashboard → `devskyy-dashboard` → Settings → Environment Variables

Add these 3 variables:

```bash
NEXT_PUBLIC_API_URL=https://devskyy.onrender.com
BACKEND_URL=https://devskyy.onrender.com
NEXT_PUBLIC_WORDPRESS_URL=https://skyyrose.com
```

### Step 2: Deploy (1 min)

**Option A** (Recommended):
```bash
git push origin main  # Auto-deploy on push
```

**Option B** (Manual):
```bash
cd /Users/coreyfoster/DevSkyy/frontend
npx vercel --prod
```

### Step 3: Verify (5 min)

```bash
# Automated check
./scripts/verify-deployment.sh https://devskyy-dashboard.vercel.app

# Manual check
open https://devskyy-dashboard.vercel.app/ai-tools
```

---

## 🔍 Verification Points

Visit `/ai-tools` and check:

- [ ] 🎲 3D Model Converter loads
- [ ] 🔍 Flux Upscaler loads
- [ ] 📊 LoRA Training Monitor loads
- [ ] 🔬 Product Analyzer loads
- [ ] 📸 Product Photography loads
- [ ] Tab navigation works
- [ ] Fullscreen toggle works
- [ ] Search/filters work

---

## 📚 Full Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| **Quick Start** | 5-minute deploy | `/docs/deployment/VERCEL_QUICK_START.md` |
| **Full Guide** | Complete reference | `/docs/deployment/VERCEL_DEPLOYMENT_GUIDE.md` |
| **HF Spaces** | Spaces integration | `/docs/HUGGINGFACE_SPACES.md` |
| **Summary** | What was done | `/docs/deployment/DEPLOYMENT_SUMMARY.md` |

---

## 🎯 Key URLs

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Production URL**: https://devskyy-dashboard.vercel.app (expected)
- **AI Tools Page**: https://devskyy-dashboard.vercel.app/ai-tools
- **Backend API**: https://devskyy.onrender.com

---

## ⚠️ Troubleshooting

**Build failed?**
```bash
cd frontend && npm run build  # Test locally
```

**Spaces not loading?**
- Check if HuggingFace spaces are public
- Test space URLs in browser
- Check browser console for errors

**Backend connection failed?**
```bash
curl https://devskyy.onrender.com/api/v1/health
```

**Need help?**
- See `/docs/deployment/VERCEL_DEPLOYMENT_GUIDE.md`
- Create issue: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

## ✅ Success Metrics

After deployment:
- ✅ Frontend loads in < 3 seconds
- ✅ All 5 HuggingFace Spaces accessible
- ✅ Navigation works on mobile
- ✅ Backend API connected
- ✅ No console errors

---

**Ready to deploy?** Follow the 3 steps above! 🚀

**Questions?** Read the full guides in `/docs/deployment/`
