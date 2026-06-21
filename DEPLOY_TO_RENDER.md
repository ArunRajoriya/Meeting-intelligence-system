# 🚀 Deploy to Render.com - Complete Guide

## Why Render?

- ✅ **Free tier** available
- ✅ **Supports FastAPI** (Python backend)
- ✅ **Supports static sites** (React frontend)
- ✅ **Easy to use** (GitHub integration)
- ✅ **Better than Vercel** for full-stack Python apps

## Prerequisites

- GitHub account
- Render.com account (free - sign up at https://render.com)
- Your code pushed to GitHub

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Ready for deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/meeting-intelligence.git
git branch -M main
git push -u origin main
```

## Step 2: Prepare Backend for Deployment

### 2.1 Create `render.yaml` (for backend)

Create this file in the root directory:

```yaml
services:
  # Backend API
  - type: web
    name: meeting-intelligence-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: GROQ_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: ASSEMBLYAI_API_KEY
        sync: false
    healthCheckPath: /health
```

### 2.2 Update `requirements.txt`

Make sure it includes all dependencies:

```txt
fastapi
uvicorn[standard]
groq
openai
python-multipart
pydantic
pydantic-settings
python-dotenv
gtts
assemblyai
pydub
numpy
sounddevice
soundfile
pyaudio
```

### 2.3 Create `.env.example`

```env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
LLAMA_MODEL=llama-3.3-70b-versatile
```

## Step 3: Deploy Backend to Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Click "New +"** → **"Web Service"**

3. **Connect GitHub Repository**
   - Select your meeting-intelligence repo
   - Click "Connect"

4. **Configure Service**:
   - **Name**: `meeting-intelligence-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

5. **Add Environment Variables**:
   - Click "Advanced" → "Add Environment Variable"
   - Add each from your `.env` file:
     - `GROQ_API_KEY` = your actual key
     - `OPENAI_API_KEY` = your actual key
     - `ASSEMBLYAI_API_KEY` = your actual key
     - `LLAMA_MODEL` = llama-3.3-70b-versatile

6. **Click "Create Web Service"**

7. **Wait for deployment** (3-5 minutes)

8. **Copy your backend URL**: 
   - Will be like: `https://meeting-intelligence-api.onrender.com`

## Step 4: Update Frontend for Production

### 4.1 Update `api.js`

```javascript
// frontend/src/services/api.js

// Use environment variable or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### 4.2 Create `.env.production` in frontend folder

```env
VITE_API_URL=https://meeting-intelligence-api.onrender.com
```

## Step 5: Deploy Frontend to Vercel

### 5.1 Update Vercel Environment Variables

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://meeting-intelligence-api.onrender.com` (your Render backend URL)
   - **Environment**: Production, Preview, Development

### 5.2 Redeploy Frontend

```bash
# In frontend directory
npm run build

# Push to GitHub (triggers Vercel deployment)
git add .
git commit -m "Configure production API URL"
git push
```

Or use Vercel CLI:
```bash
vercel --prod
```

## Step 6: Update Backend CORS

Make sure your backend (`main.py`) allows your Vercel frontend:

```python
# main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Push this change to trigger Render redeployment.

## Step 7: Test Deployment

1. **Test Backend**:
   ```bash
   curl https://meeting-intelligence-api.onrender.com/health
   ```
   Should return: `{"status":"healthy"}`

2. **Test Frontend**:
   - Open your Vercel URL: `https://your-app.vercel.app`
   - Try starting a meeting
   - Should connect to Render backend

## Troubleshooting

### Backend not starting on Render

**Check Logs**:
1. Go to Render Dashboard
2. Click your service
3. Click "Logs" tab
4. Look for errors

**Common Issues**:
- Missing dependencies in `requirements.txt`
- Missing environment variables
- Port binding (use `$PORT` not `8000`)

### Frontend can't connect to backend

**Check**:
1. Backend is running (visit `/health` endpoint)
2. CORS settings allow your Vercel domain
3. `VITE_API_URL` environment variable is set correctly
4. Frontend is using HTTPS (Vercel), backend is HTTPS (Render)

### "Mixed Content" error

**Issue**: Frontend on HTTPS, backend on HTTP

**Solution**: 
- Render automatically provides HTTPS
- Make sure you're using `https://` in `VITE_API_URL`

## Cost

### Free Tier Limits

**Render Free Tier**:
- 750 hours/month
- Spins down after 15 min inactivity
- Spin up time: 30-60 seconds on first request
- Sufficient for personal projects

**Vercel Free Tier**:
- Unlimited bandwidth
- 100 GB-hours execution
- Perfect for frontend

### Going Production

**If you need always-on**:
- Render Starter: $7/month
- Railway Starter: $5/month
- Both provide 24/7 uptime

## Alternative: All-in-One Deployment

### Option A: Deploy Everything on Render

Deploy frontend as Static Site on Render too (instead of Vercel).

**Pros**: Everything in one place  
**Cons**: Vercel is better optimized for React

### Option B: Use Railway.app

Railway supports both backend and frontend with great DX.

**Steps**:
1. Go to railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Railway auto-detects FastAPI + React
5. Set environment variables
6. Done!

## Summary

**Recommended Setup**:
- ✅ Backend: Render.com (Free)
- ✅ Frontend: Vercel (Free)
- ✅ Total Cost: $0
- ✅ Production-ready: Yes

**Your URLs**:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://meeting-intelligence-api.onrender.com`
- Both connected via environment variables

---

**Need Help?**
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
