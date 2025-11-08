# Deploy Voice Recognition API to Railway

## Steps to Deploy

### 1. Push Current Branch to GitHub
```bash
git push origin john/voice-training
```

### 2. Create New Railway Service

**Option A: Via Railway Dashboard**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose: `Harrisous/2025-AI-Hackathon`
5. Select branch: `john/voice-training`
6. Railway will auto-detect and deploy

**Option B: Via Railway CLI**
```bash
# Login
railway login --browserless

# Create new project
railway init

# Link to this directory
railway link

# Deploy
railway up

# Generate domain
railway domain
```

### 3. Add Environment Variables

In Railway dashboard, add these variables:
```
SUPABASE_URL=https://aidxatmmfpmhxxpkmnny.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFpZHhhdG1tZnBtaHh4cGttbm55Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1NTk3ODgsImV4cCI6MjA3ODEzNTc4OH0.MO26zZJUR4vZscB-QlE_Wr6TTXMaQb29JyLHNgvAbvQ
```

### 4. Upload Voice Profile

The `patient_voice_robust.pkl` file needs to be in the deployment.
It's already in the repository, so Railway will have it.

### 5. Test the Deployment

Once deployed, test with:
```bash
curl https://your-new-railway-url.up.railway.app/health
```

Then test voice verification:
```bash
curl -X POST \
  -F "audio=@test_audio.wav" \
  https://your-new-railway-url.up.railway.app/verify/voice
```

---

## Alternative: Merge to Existing Deployment

If you want to use the same Railway service:

```bash
# Switch to deployment branch
git checkout john/raspberry-confirmation

# Merge voice training
git merge john/voice-training

# Push
git push origin john/raspberry-confirmation
```

Railway will auto-redeploy with the new `/verify/voice` endpoint.

---

## Files Needed for Deployment

✅ Already in repository:
- `app.py` (with /verify/voice endpoint)
- `robust_voice_system.py`
- `patient_voice_robust.pkl` (voice profile)
- `requirements.txt` (with resemblyzer)
- `Procfile`

---

## Expected Deployment Time

- Build: ~5-10 minutes (installing resemblyzer and dependencies)
- First request: ~30 seconds (loading voice model)
- Subsequent requests: <1 second

---

## Which Option Do You Prefer?

1. **New Railway Service** - Separate voice API
2. **Merge to Existing** - Same API, add /verify/voice endpoint
