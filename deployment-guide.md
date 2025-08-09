# Deployment Guide: Vercel + Railway

## Backend Deployment (Railway)

### 1. Prepare your FastAPI app for Railway

Create `railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
```

### 2. Environment Variables for Railway

```bash
DATABASE_URL=postgresql://username:password@host:port/dbname
CLERK_SECRET_KEY=your_clerk_secret
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

### 3. Deploy to Railway

1. Connect your GitHub repo to Railway
2. Railway auto-detects Python and installs dependencies
3. Your API will be available at: `https://your-app.railway.app`

## Frontend Deployment (Vercel)

### 1. Prepare React app for Vercel

Create `vercel.json` in your React project:

```json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "headers": {
        "cache-control": "s-maxage=31536000,immutable"
      }
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### 2. Environment Variables for Vercel

```bash
REACT_APP_API_URL=https://your-app.railway.app
REACT_APP_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

### 3. Deploy to Vercel

1. Connect your GitHub repo to Vercel
2. Set build command: `npm run build`
3. Set output directory: `build`
4. Your frontend will be available at: `https://your-app.vercel.app`

## Cost Breakdown

- **Railway**: Free tier with PostgreSQL
- **Vercel**: Free tier for personal projects
- **Total**: $0/month (with free tier limitations)

## Upgrading Later

- **Railway Pro**: $5/month for no sleep mode
- **Vercel Pro**: $20/month for team features
