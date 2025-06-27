# 🚀 Deployment Guide: Bilingual MCP Terminology Checker

## Prerequisites ✅
- [x] Render account (render.com) 
- [x] Streamlit Community Cloud account (share.streamlit.io)
- [x] OpenAI API key (optional but recommended)
- [x] GitHub repository pushed

## Step 1: Deploy Backend API to Render 🔧

### 1.1 Create New Web Service
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub account if not connected
4. Select repository: `wy-yang-lab/Bilingual_MCP`
5. Click "Connect"

### 1.2 Configure Service Settings
```
Name: bilingual-mcp-api
Environment: Docker
Region: Oregon (US West) or closest to you
Branch: main
Build Command: (leave blank - using Dockerfile)
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 1.3 Set Environment Variables
Add these environment variables in Render:
```
API_TOKEN=your-secure-token-here
OPENAI_API_KEY=sk-your-openai-key-here
DEBUG=false
```

### 1.4 Deploy
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Test: `https://your-app-name.onrender.com/health`
4. Should return: `{"status": "healthy", "llm_available": true}`

## Step 2: Deploy Frontend UI to Streamlit Cloud ⚡

### 2.1 Create New App
1. Go to https://share.streamlit.io
2. Click "New app"
3. Repository: `wy-yang-lab/Bilingual_MCP`
4. Branch: `main`
5. Main file path: `ui_app.py`
6. App URL: `bilingual-mcp-ui` (or your choice)

### 2.2 Set Environment Variables
In "Advanced settings" → "Environment variables":
```
API_BASE_URL=https://your-render-app.onrender.com
AUTH_TOKEN=your-secure-token-here
```

### 2.3 Deploy
1. Click "Deploy!"
2. Wait for deployment (3-5 minutes)
3. Test: Your app will be at `https://bilingual-mcp-ui.streamlit.app`

## Step 3: Final Configuration 🔒

### 3.1 Update CORS (Optional)
After deployment, you can tighten CORS in `app/core/config.py`:
```python
ALLOWED_ORIGINS: List[str] = [
    "https://bilingual-mcp-ui.streamlit.app",
    "http://localhost:8501"  # Keep for local development
]
```

### 3.2 Test Full Integration
1. Go to your Streamlit app URL
2. Enter test text: "Please login to access your e-mail account"
3. Select "🇺🇸 English"
4. Check "🤖 Use AI analysis" (if you have OpenAI key)
5. Click "🔍 Analyze Terminology"
6. Should see suggestions like: "e-mail" → "email"

## 🎯 Your Live URLs
- **API Backend**: `https://your-render-app.onrender.com`
- **UI Frontend**: `https://your-streamlit-app.streamlit.app`
- **API Docs**: `https://your-render-app.onrender.com/docs`
- **Health Check**: `https://your-render-app.onrender.com/health`

## 💡 Tips for Recruiters
1. **Demo Flow**: Show both English and Japanese text analysis
2. **Professional Data**: Mention 189k+ Microsoft terminology entries
3. **AI Integration**: Toggle LLM analysis on/off to show difference
4. **Real-time**: Emphasize instant feedback for UI developers
5. **Standards Compliance**: Highlight MCP protocol compatibility

## 🐛 Troubleshooting
- **API not responding**: Check Render logs, verify environment variables
- **CORS errors**: Ensure Streamlit URL is in ALLOWED_ORIGINS
- **LLM not working**: Verify OPENAI_API_KEY is set correctly
- **Database issues**: Check if terms.db is included in Docker build

## 💰 Costs
- **Render**: Free tier (750 hours/month)
- **Streamlit**: Completely free
- **OpenAI**: ~$0.01 per terminology check with GPT-4o
- **Total**: Essentially free for demo purposes

---
**Ready for production!** 🚀 