# 🔧 Fix Vercel Deployment - Connect to Render Backend

## Current Setup

✅ **Backend**: Already deployed on Render  
   - URL: https://ai-powered-meeting-intelligence-platform.onrender.com  

⚠️ **Frontend**: Deployed on Vercel but pointing to wrong backend  
   - Was pointing to: `http://localhost:8000` (doesn't work in production!)  
   - Should point to: `https://ai-powered-meeting-intelligence-platform.onrender.com`  

## Quick Fix (3 Steps)

### Step 1: Update Frontend Environment Variable

**On Vercel Dashboard:**

1. Go to your Vercel project: https://vercel.com/dashboard
2. Select your meeting intelligence project
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://ai-powered-meeting-intelligence-platform.onrender.com`
   - **Environments**: Check all (Production, Preview, Development)
5. Click **Save**

### Step 2: Push Updated Code to Trigger Redeploy

The code changes have been made locally. Now push to GitHub:

```bash
# In your project root
git add .
git commit -m "Fix: Connect Vercel frontend to Render backend"
git push origin main
```

This will automatically trigger a Vercel redeployment with the new environment variable.

**Alternative: Manual Redeploy**
1. Go to Vercel Dashboard
2. Click your project
3. Go to **Deployments** tab
4. Click **⋯** (three dots) on latest deployment
5. Click **Redeploy**
6. Check "Use existing Build Cache" (faster)
7. Click **Redeploy**

### Step 3: Update Backend CORS (Already Done!)

The `main.py` file has been updated to allow Vercel domains.

**Push to Render:**
```bash
git add main.py
git commit -m "Fix: Allow Vercel domains in CORS"
git push origin main
```

Render will automatically redeploy the backend (takes 2-3 minutes).

## Verify Deployment

### Test Backend Health

```bash
curl https://ai-powered-meeting-intelligence-platform.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Meeting Intelligence System",
  "version": "2.0.0"
}
```

### Test Frontend Connection

1. Open your Vercel app (e.g., `https://your-app.vercel.app`)
2. Open browser DevTools (F12)
3. Go to **Console** tab
4. Look for: `🔗 API Base URL: https://ai-powered-meeting-intelligence-platform.onrender.com`
5. Try starting a meeting
6. Should work now! ✅

## Files Changed

✅ `frontend/.env.production` - Added production API URL  
✅ `frontend/.env.local` - Added local development API URL  
✅ `frontend/src/services/api.js` - Updated to use environment variable  
✅ `main.py` - Updated CORS to allow Vercel domains  

## Troubleshooting

### Error: "Network Error" or "Failed to start meeting"

**Check 1: Backend is running**
```bash
curl https://ai-powered-meeting-intelligence-platform.onrender.com/health
```
If this fails, your Render backend is down (might be spinning up - wait 60 seconds).

**Check 2: CORS is set correctly**
Open browser DevTools → Network tab, try starting a meeting, check if you see CORS errors.

**Check 3: Environment variable is set**
In Vercel dashboard, verify `VITE_API_URL` is set correctly.

### Error: "Mixed Content" warning

**Issue**: Frontend is HTTPS, backend is HTTP  
**Solution**: Your Render backend already uses HTTPS, so this shouldn't happen.

### Backend URL not updating

**Solution**: Clear Vercel build cache
1. Go to Vercel Dashboard
2. Settings → General
3. Scroll to "Build & Development Settings"
4. Click "Clear Cache"
5. Redeploy

### Render backend is slow (first request)

**Issue**: Free tier spins down after 15 min inactivity  
**Solution**: 
- First request takes 30-60 seconds to spin up
- This is normal for free tier
- Consider upgrading to $7/month for always-on

## Important Notes

### Render Free Tier Behavior

⚠️ **Spin Down**: Backend sleeps after 15 minutes of inactivity  
⏱️ **Spin Up**: Takes 30-60 seconds on first request  
💡 **User Experience**: Add loading message: "Starting backend (can take up to 60 seconds)..."  

### Local Development

For local dev, the system automatically uses `http://localhost:8000`:
```bash
# Backend
python main.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

The `.env.local` file ensures local development uses localhost.

## Production Checklist

Before going live:

- [ ] Backend is deployed on Render and accessible
- [ ] Frontend is deployed on Vercel
- [ ] `VITE_API_URL` environment variable is set on Vercel
- [ ] CORS allows Vercel domain in `main.py`
- [ ] Both deployments are up-to-date with latest code
- [ ] Health check works: `/health` endpoint returns 200
- [ ] Can start/stop meetings on production
- [ ] Audio transcription works on production
- [ ] WebSocket connection works (for live audio)

## Cost Summary

**Current Setup (Free Tier):**
- Render Backend: $0/month (750 hours free)
- Vercel Frontend: $0/month (unlimited)
- Total: **$0/month**

**Limitations:**
- Backend spins down after 15 min
- Cold start takes 30-60s
- Suitable for demos and personal use

**Upgrade Options:**
- Render Starter ($7/mo): Always-on backend
- Railway Starter ($5/mo): Alternative platform
- Both provide 24/7 uptime

---

## Next Steps

1. **Push code to GitHub** (triggers Vercel redeploy)
2. **Set environment variable** on Vercel dashboard
3. **Wait 2-3 minutes** for both deployments to complete
4. **Test on production** - try starting a meeting
5. **Celebrate** 🎉 Your full-stack app is live!

**Need the Vercel URL?**  
Check your Vercel dashboard: https://vercel.com/dashboard
