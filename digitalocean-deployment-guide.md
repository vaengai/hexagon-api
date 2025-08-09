# DigitalOcean App Platform Deployment

## Why Choose DigitalOcean?

- ✅ Simple one-platform solution
- ✅ No sleep mode (always available)
- ✅ Automatic scaling
- ✅ Built-in PostgreSQL
- ✅ $5/month starter plan

## Step-by-Step Deployment

### 1. Prepare Your App Spec

Create `.do/app.yaml`:

```yaml
name: hexagon-app
services:
  - name: api
    source_dir: /
    github:
      repo: vaengai/hexagon-api
      branch: main
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8080
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: CLERK_SECRET_KEY
        scope: RUN_TIME
        value: your_clerk_secret_key
      - key: CLERK_PUBLISHABLE_KEY
        scope: RUN_TIME
        value: your_clerk_publishable_key

  - name: frontend
    source_dir: /frontend # assuming you have a frontend folder
    github:
      repo: vaengai/hexagon-frontend
      branch: main
    build_command: npm run build
    run_command: serve -s build -l 3000
    environment_slug: node-js
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 3000
    routes:
      - path: /
    envs:
      - key: REACT_APP_API_URL
        scope: BUILD_TIME
        value: ${api.PUBLIC_URL}
      - key: REACT_APP_CLERK_PUBLISHABLE_KEY
        scope: BUILD_TIME
        value: your_clerk_publishable_key

databases:
  - name: db
    engine: PG
    version: "14"
    size: basic-xs
    num_nodes: 1
```

### 2. Deploy via DigitalOcean Console

1. **Create Account**: Sign up at digitalocean.com
2. **Connect Repository**: Link your GitHub account
3. **Select Repository**: Choose your hexagon-api repo
4. **Configure App**: Use the app spec above
5. **Add Database**: Select PostgreSQL starter plan
6. **Deploy**: Click "Create Resources"

### 3. Environment Variables Setup

In DigitalOcean console:

```bash
# App-level environment variables
DATABASE_URL=${db.DATABASE_URL}  # Auto-generated
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Frontend build-time variables
REACT_APP_API_URL=${api.PUBLIC_URL}
REACT_APP_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 4. Custom Domain (Optional)

```bash
# Add custom domain in DigitalOcean console
# Point your DNS to:
# Frontend: your-app.ondigitalocean.app
# API: your-app-api.ondigitalocean.app
```

## Pricing Breakdown

### Starter Plan ($5/month)

- **API Service**: Basic XXS ($5/month)
- **Frontend Service**: Basic XXS ($5/month)
- **PostgreSQL Database**: Basic XS ($7/month)
- **Total**: ~$17/month

### Development Plan ($12/month)

- **API Service**: Basic XS ($12/month)
- **Database**: Basic XS ($7/month)
- **Frontend**: Can use Vercel free tier
- **Total**: ~$19/month

## Advantages

- Zero configuration scaling
- Automatic SSL certificates
- Built-in monitoring
- No server maintenance
- Direct GitHub integration

## When to Choose This

- You want simplicity over cost optimization
- You need 24/7 availability (no sleep mode)
- You prefer managed services
- Budget allows $15-20/month
