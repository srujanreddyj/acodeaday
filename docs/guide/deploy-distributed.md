# Distributed Deployment

Deploy acodeaday components on different platforms for flexibility and scaling.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│    Judge0       │
│  Vercel/Netlify │     │ Railway/Fly.io  │     │  VPS/RapidAPI   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Database      │
                        │   Supabase      │
                        └─────────────────┘
```

## Component Deployment

### Frontend

**Recommended platforms:** Vercel, Netlify, Cloudflare Pages

The frontend is a TanStack Start (React) application with SSR.

#### Deploy to Vercel

1. Connect your GitHub repo to Vercel
2. Set the root directory to `frontend`
3. Configure environment variables:

```
VITE_API_URL=https://api.yourdomain.com
VITE_SUPABASE_URL=https://[project].supabase.co
VITE_SUPABASE_KEY=[your-anon-key]
```

4. Deploy

#### Deploy to Netlify

1. Connect your GitHub repo
2. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `.output/public`
3. Add environment variables (same as Vercel)
4. Deploy

#### Using Docker Image

```bash
docker pull ghcr.io/engineeringwithtemi/acodeaday-frontend:latest

docker run -d \
  -p 3000:3000 \
  -e VITE_API_URL=https://api.yourdomain.com \
  -e VITE_SUPABASE_URL=https://[project].supabase.co \
  -e VITE_SUPABASE_KEY=[your-anon-key] \
  ghcr.io/engineeringwithtemi/acodeaday-frontend:latest
```

---

### Backend

**Recommended platforms:** Railway, Fly.io, Render

The backend is a FastAPI (Python) application.

#### Deploy to Railway

1. Create new project from GitHub repo
2. Set root directory to `backend`
3. Configure environment variables:

```
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=[your-anon-key]
JUDGE0_URL=https://your-judge0-url.com
ENVIRONMENT=production
LOG_LEVEL=INFO
```

4. Optional (for AI chat):
```
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

5. Deploy - migrations run automatically on startup

#### Deploy to Fly.io

1. Install Fly CLI: `brew install flyctl`
2. Create app:

```bash
cd backend
fly launch --no-deploy
```

3. Set secrets:

```bash
fly secrets set DATABASE_URL="postgresql+asyncpg://..." \
  SUPABASE_URL="https://..." \
  SUPABASE_KEY="..." \
  JUDGE0_URL="https://..."
```

4. Deploy:

```bash
fly deploy
```

#### Deploy to Render

1. Create new Web Service from GitHub repo
2. Root directory: `backend`
3. Build command: `pip install uv && uv sync`
4. Start command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

#### Using Docker Image

```bash
docker pull ghcr.io/engineeringwithtemi/acodeaday-backend:latest

docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SUPABASE_URL=https://... \
  -e SUPABASE_KEY=... \
  -e JUDGE0_URL=https://... \
  ghcr.io/engineeringwithtemi/acodeaday-backend:latest
```

---

### Judge0 (Code Execution)

Judge0 is resource-intensive and requires privileged Docker mode.

#### Option 1: Self-hosted VPS (Recommended)

Best for production - no rate limits, full control.

**Requirements:**
- VPS with 2+ CPU cores, 4GB+ RAM
- Docker with privileged container support

**Setup:**

```bash
# Create judge0-compose.yml with just Judge0 services
curl -O https://raw.githubusercontent.com/engineeringwithtemi/acodeaday/main/docker-compose.yml

# Extract Judge0 services or use this minimal config:
cat > judge0-compose.yml << 'EOF'
services:
  judge0-server:
    image: judge0/judge0:1.13.1
    command: ["bash", "-c", "sudo mkdir -p /box && sudo chmod 1777 /box && exec ./scripts/server"]
    ports:
      - "2358:2358"
    privileged: true
    environment:
      - REDIS_HOST=judge0-redis
      - POSTGRES_HOST=judge0-db
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=judge0password
      - POSTGRES_DB=judge0
      - ENABLE_WAIT_RESULT=true
    depends_on:
      - judge0-db
      - judge0-redis

  judge0-workers:
    image: judge0/judge0:1.13.1
    command: ["bash", "-c", "sudo mkdir -p /box && sudo chmod 1777 /box && exec ./scripts/workers"]
    privileged: true
    environment:
      - REDIS_HOST=judge0-redis
      - POSTGRES_HOST=judge0-db
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=judge0password
      - POSTGRES_DB=judge0

  judge0-db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=judge0password
      - POSTGRES_DB=judge0
    volumes:
      - judge0-postgres-data:/var/lib/postgresql/data

  judge0-redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - judge0-redis-data:/data

volumes:
  judge0-postgres-data:
  judge0-redis-data:
EOF

# Start Judge0
docker compose -f judge0-compose.yml up -d
```

Configure your backend with:
```
JUDGE0_URL=http://your-vps-ip:2358
```

#### Option 2: RapidAPI (Hosted)

For low-traffic use or testing.

1. Sign up at [RapidAPI Judge0](https://rapidapi.com/judge0-judge0-default/api/judge0-ce)
2. Get your API key
3. Configure backend:

```
JUDGE0_URL=https://judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=your-rapidapi-key
```

::: warning
RapidAPI free tier is limited to 50 requests/day. For regular use, self-host Judge0.
:::

---

## Connecting Components

### CORS Configuration

The backend must allow requests from your frontend domain.

Update `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend → Backend

Set `VITE_API_URL` to your backend's public URL:

```
VITE_API_URL=https://api.yourdomain.com
```

Or if using a subdomain:

```
VITE_API_URL=https://backend.yourdomain.com
```

### Backend → Judge0

Set `JUDGE0_URL` to your Judge0 instance:

```
JUDGE0_URL=http://your-judge0-vps:2358
```

If Judge0 is behind a firewall, ensure your backend's IP can reach it.

---

## Cost Comparison

| Setup | Frontend | Backend | Judge0 | Database | Total |
|-------|----------|---------|--------|----------|-------|
| Free Tier | Vercel Free | Railway Free ($5 credit) | RapidAPI Free | Supabase Free | $0/mo |
| Production | Vercel Pro ($20) | Railway ($5-20) | VPS ($10-20) | Supabase Pro ($25) | ~$60-85/mo |
| Self-Hosted | VPS ($5) | Same VPS | Same VPS | Supabase Free | ~$5-10/mo |

---

## Troubleshooting

### CORS errors in browser

**Problem:** Frontend can't make requests to backend.

**Solution:** Add your frontend domain to CORS allowed origins in the backend.

### Judge0 timeout

**Problem:** Code execution times out.

**Solution:**
- Check if Judge0 is running: `curl http://your-judge0:2358/about`
- Ensure backend can reach Judge0 (firewall rules)
- Check Judge0 worker logs: `docker logs judge0-workers`

### Database connection issues

**Problem:** Backend can't connect to Supabase.

**Solution:**
- Use the pooler URL (port 6543) for serverless deployments
- Verify your IP is allowed in Supabase network settings
- Check connection string format: `postgresql+asyncpg://`

### Environment variables not loading

**Problem:** Frontend shows API errors.

**Solution:**
- Verify `VITE_` prefix for all frontend env vars
- Redeploy after changing environment variables
- Check browser network tab for actual API URL being used

---

## Next Steps

- [Self-Hosting Overview](/guide/self-hosting) - Other deployment options
- [Deploy to Coolify](/guide/deploy-coolify) - PaaS alternative
- [Environment Variables](/guide/environment-variables) - Complete reference
