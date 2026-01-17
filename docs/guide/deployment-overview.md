# Deployment Overview

This guide covers deploying acodeaday to production. Choose the deployment method that fits your needs.

## Quick Decision Guide

| I want to...                | Use this guide                                      |
| --------------------------- | --------------------------------------------------- |
| Run locally for development | [Quick Start](/guide/quick-start)                   |
| Self-host on my own server  | [Self-Hosting](/guide/self-hosting)                 |
| Deploy with Coolify/PaaS    | [Deploy to Coolify](/guide/deploy-coolify)          |
| Use Vercel + Railway + VPS  | [Distributed Deployment](/guide/deploy-distributed) |
| Deploy just the backend     | [Deploy Backend](/guide/deploy-backend)             |
| Deploy just the frontend    | [Deploy Frontend](/guide/deploy-frontend)           |

## Security: Change Default Credentials

::: danger IMPORTANT
Before deploying to production, you **must** change the default credentials. Leaving defaults exposes your application to unauthorized access.
:::

### Credentials to Change

| Variable          | Default                       | Where to Change |
| ----------------- | ----------------------------- | --------------- |
| `AUTH_USER_EMAIL` | `admin@acodeaday.vercel.app`  | `.env` file     |
| `AUTH_PASSWORD`   | `changeme`                    | `.env` file     |

### How to Generate Secure Passwords

```bash
# Generate a random 32-character password
openssl rand -base64 32
```

### Example Secure Configuration

```bash
# In your .env file
AUTH_USER_EMAIL=your_email@example.com
AUTH_PASSWORD=K8xP2mN9vL4wQ7jR3hF6tY1bC5gA0sD8
```

::: tip
Use a password manager to generate and store unique passwords for each service.
:::

## Architecture

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Frontend       │─────▶│   Backend        │─────▶│   Judge0         │
│   (Static)       │      │   (FastAPI)      │      │   (Docker)       │
│   Vercel/Netlify │      │   Railway/Fly.io │      │   Self-hosted    │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │   Database       │
                          │   Supabase       │
                          └──────────────────┘
```

## Components

### 1. Frontend (Static Site)

The React frontend builds to static HTML/CSS/JS files.

**Recommended Platforms:**

- **Vercel** (easiest, free tier)
- **Netlify** (free tier)
- **Cloudflare Pages** (free tier)
- **AWS S3 + CloudFront**
- **GitHub Pages**

**Requirements:**

- Node.js 22+ build environment
- Environment variables for API URL and Supabase

### 2. Backend (Python API)

The FastAPI backend is a Python ASGI application.

**Recommended Platforms:**

- **Railway** (easiest, free tier)
- **Fly.io** (free tier, more control)
- **Render** (free tier)
- **AWS Elastic Beanstalk**
- **Google Cloud Run**
- **DigitalOcean App Platform**

**Requirements:**

- Python 3.12+
- PostgreSQL connection (Supabase)
- Judge0 API access
- Environment variables

### 3. Judge0 (Code Execution)

Judge0 requires Docker and is resource-intensive.

**Options:**

**Self-hosted (Recommended for production):**

- VPS (DigitalOcean, Linode, AWS EC2)
- Minimum: 2 CPU cores, 4 GB RAM
- Runs via Docker Compose

**Hosted Service:**

- [RapidAPI Judge0](https://rapidapi.com/judge0-judge0-default/api/judge0-ce)
- Free tier: 50 requests/day
- Paid tiers available

### 4. Database

**Supabase (Recommended):**

- Managed PostgreSQL
- Free tier: 500 MB storage
- Includes auth, real-time features

**Alternatives:**

- AWS RDS PostgreSQL
- Google Cloud SQL
- Neon (serverless Postgres)
- Self-hosted PostgreSQL

## Deployment Strategies

### Strategy 1: Maximum Free Tier

Perfect for personal projects and testing.

- **Frontend**: Vercel (free)
- **Backend**: Railway (free tier, $5 credit)
- **Database**: Supabase (free tier)
- **Judge0**: RapidAPI Judge0 (free tier, limited)

**Pros:**

- $0/month cost
- Easy setup
- Good for low traffic

**Cons:**

- Judge0 rate limits (50 requests/day)
- Railway free tier has limits

### Strategy 2: Scalable Production

For real-world production use with higher traffic.

- **Frontend**: Vercel (free tier or $20/month Pro)
- **Backend**: Railway (free tier or $5-20/month)
- **Database**: Supabase (free tier or $25/month Pro)
- **Judge0**: Self-hosted VPS ($10-20/month)

::: info Free tiers work for production
All these platforms offer free tiers that can handle production workloads for small to medium traffic. Paid tiers are only necessary when you exceed free tier limits or need additional features.
:::

**Pros:**

- No rate limits (with paid tiers)
- Full control
- Scales with usage

**Cons:**

- Monthly costs
- Requires DevOps knowledge for Judge0

### Strategy 3: Self-Hosted Everything

Maximum control and privacy.

- **All components**: Single VPS or Kubernetes cluster
- **Cost**: Varies depending on the server provider you use

**Pros:**

- Full control
- Data privacy
- Predictable costs

**Cons:**

- Requires DevOps expertise
- Manual scaling
- Maintenance overhead

## Pre-Deployment Checklist

Before deploying, ensure you have:

### Backend

- [ ] All tests passing (`uv run pytest`)
- [ ] Environment variables documented
- [ ] Database migrations up to date
- [ ] Seed data ready
- [ ] CORS configured for production domain
- [ ] Secrets stored securely (not in code)

### Frontend

- [ ] Production build works (`npm run build`)
- [ ] Environment variables configured
- [ ] API URLs point to production
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Analytics configured (optional)

### Database

- [ ] Supabase project created
- [ ] Backups enabled
- [ ] Connection pooling configured
- [ ] SSL required

### Judge0

- [ ] VPS provisioned (if self-hosting)
- [ ] Docker Compose configured
- [ ] Authentication enabled
- [ ] Resource limits set
- [ ] Monitoring configured

## Security Considerations

### Backend

- Use HTTPS only
- Enable CORS only for your frontend domain
- Store secrets in environment variables
- Use Supabase Row Level Security (RLS)
- Rate limit API endpoints
- Validate all user inputs

### Judge0

- Enable authentication
- Use private network if possible
- Set resource limits (CPU, memory, time)
- Monitor for abuse
- Use firewall rules

### Database

- Require SSL connections
- Use strong passwords
- Enable Supabase RLS policies
- Limit database access to backend only
- Enable audit logging
- Regular backups

## Monitoring

### Application Monitoring

- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Datadog**: Full-stack monitoring

### Infrastructure Monitoring

- **Uptime checks**: UptimeRobot, Pingdom
- **Logs**: Papertrail, Logtail
- **Metrics**: Prometheus, Grafana

### Judge0 Monitoring

- Docker stats: `docker stats`
- Resource usage
- Submission queue length
- Error rates

## Backup Strategy

### Database Backups

- **Supabase**: Automatic daily backups (Pro plan)
- **Manual**: Daily `pg_dump` via cron job
- Store in S3 or similar

### Code Backups

- Git repository (GitHub, GitLab)
- Tag releases
- Document deployment process

### Configuration Backups

- Store `.env.example` files
- Document infrastructure as code
- Keep deployment scripts in Git

## Rollback Plan

1. **Keep previous version deployed** (blue-green deployment)
2. **Database migrations**: Use reversible migrations
3. **Frontend**: Keep previous build artifacts
4. **Monitoring**: Set up alerts for errors/downtime

## Next Steps

Choose your deployment strategy, then proceed with specific guides:

### Self-Hosting

- [Self-Hosting Guide](/guide/self-hosting) - Complete self-hosting options
- [Deploy to Coolify](/guide/deploy-coolify) - PaaS deployment with Coolify
- [Distributed Deployment](/guide/deploy-distributed) - Deploy on multiple platforms

### Cloud Platforms

- [Deploy Backend](/guide/deploy-backend) - Railway, Fly.io, Render
- [Deploy Frontend](/guide/deploy-frontend) - Vercel, Netlify, Cloudflare

### Reference

- [Environment Variables](/guide/environment-variables) - Complete configuration reference
