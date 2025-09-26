# F1 ELO Deployment Guide

This guide explains how to deploy your F1 Performance Metrics application to free hosting platforms.

## 🚀 Deployment Options

We recommend using **Streamlit Community Cloud** for the frontend and **Render** for the backend.

## 📦 Backend Deployment (Render)

### Step 1: Prepare Repository
1. Push your code to GitHub (make sure it's public or you have a paid Render account)
2. Ensure all configuration files are committed:
   - `requirements.txt`
   - `render.yaml`
   - `Procfile`

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and sign up with GitHub
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `f1-elo-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables:
   - `ENVIRONMENT` = `production`
   - `PYTHON_VERSION` = `3.12.0`
6. Click "Create Web Service"

### Step 3: Note Your Backend URL
- Your backend will be available at: `https://your-app-name.onrender.com`
- Health check: `https://your-app-name.onrender.com/health`
- API docs: `https://your-app-name.onrender.com/docs`

## 🎨 Frontend Deployment (Streamlit Community Cloud)

### Step 1: Deploy to Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set the main file path: `frontend/app.py`
6. Click "Deploy!"

### Step 2: Configure API URL
1. In your Streamlit app dashboard, go to "Settings" → "Secrets"
2. Add the following configuration:
```toml
[api]
base_url = "https://your-render-backend-url.onrender.com/api/v1"
```
3. Replace `your-render-backend-url` with your actual Render backend URL
4. Click "Save"

### Step 3: Restart App
- Click "Reboot app" to apply the new configuration

## 🔧 Configuration Files Reference

### `.streamlit/config.toml`
```toml
[global]
developmentMode = false

[server]
headless = true
enableCORS = false
port = 8501

[theme]
primaryColor = "#FF6600"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### `requirements.txt`
Contains all Python dependencies needed for both services.

### `render.yaml`
Render deployment configuration for the backend API.

### `Procfile`
Alternative deployment configuration for Heroku-compatible platforms.

## 🌐 Alternative Deployment Options

### Option 2: Railway
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Deploy both frontend and backend
4. Configure environment variables

### Option 3: Google Cloud Run
1. Create Dockerfile for containerization
2. Build and push to Google Container Registry
3. Deploy to Cloud Run
4. Configure custom domains if needed

## ⚠️ Important Notes

### Backend Considerations
- **Cold Starts**: Free Render services sleep after 15 minutes of inactivity
- **Memory**: 512MB limit on free tier
- **Build Time**: First deployment may take 5-10 minutes

### Frontend Considerations
- **Streamlit Secrets**: Configure API URL in Streamlit Cloud secrets
- **Resource Limits**: 1GB RAM limit
- **Sleeping**: App may sleep after inactivity

### Data Considerations
- **Dataset Size**: 21MB CSV files are included in deployment
- **Cache**: Application uses file-based caching for performance
- **Persistence**: Cache resets on each deployment

## 🔍 Troubleshooting

### Backend Issues
- Check logs in Render dashboard
- Verify environment variables are set
- Test health endpoint: `https://your-backend.onrender.com/health`

### Frontend Issues
- Check Streamlit Cloud logs
- Verify secrets configuration
- Test API connection in app

### CORS Issues
- Backend automatically configures CORS for Streamlit domains
- Check browser console for CORS errors

## 📊 Monitoring

### Backend Monitoring
- Health endpoint: `/health`
- Cache stats: `/api/v1/cache/clear` (GET for stats)
- API documentation: `/docs`

### Performance Tips
- Cache is automatically configured
- API responses are optimized for speed
- Use filtering parameters to reduce data transfer

## 🎉 Success!

Once deployed, your F1 Performance Metrics application will be available at:
- **Frontend**: `https://your-streamlit-app.streamlit.app`
- **Backend API**: `https://your-render-backend.onrender.com`

Enjoy exploring F1 performance data! 🏎️