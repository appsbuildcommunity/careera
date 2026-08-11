# Careera — Deployment Guide

This document outlines the deployment strategy for the Careera platform. 

For the MVP, we highly recommend the **Serverless / PaaS (Platform as a Service)** route. It provides automated CI/CD directly from GitHub, requires zero server maintenance, and operates entirely within free tiers.

---

## 1. Recommended MVP Deployment (PaaS - Free Tier)

This approach connects your GitHub repository directly to hosting platforms. When you push to `main`, the platforms automatically build and deploy your code. No Docker or CI/CD pipeline configuration is required.

### Architecture

| Layer | Service | Rationale | Cost |
|-------|---------|-----------|------|
| **Frontend** | [Vercel](https://vercel.com) | Native Next.js support, zero-config deployments, edge caching. | Free (Hobby Tier) |
| **Backend** | [Render](https://render.com) | Native Python/FastAPI support, automated builds via `requirements.txt`. | Free (Web Service Tier) |
| **Database** | [MongoDB Atlas](https://mongodb.com) | Managed NoSQL, automated backups, highly available. | Free (M0 Cluster) |

### Deployment Steps

1. **Database:** Create a free MongoDB Atlas cluster, whitelist IP `0.0.0.0/0`, and grab the connection string.
2. **Backend (Render):** Create a new "Web Service", connect the GitHub repo, set the Build Command to `pip install -r requirements.txt`, and Start Command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. **Frontend (Vercel):** Create a new Project, connect the GitHub repo, and Vercel will auto-detect Next.js and handle the rest.

---

## 2. Environment Variables

Regardless of where you deploy, the following environment variables must be configured in your hosting dashboards:

**Backend (Render):**
```env
MONGODB_URL=mongodb+srv://<user>:<password>@cluster.mongodb.net/careera
JWT_SECRET=<super_secure_random_string>
GOOGLE_CLIENT_ID=<your_google_oauth_client_id>
LLM_PROVIDER=mock            # mock | gemini | openai | anthropic | deepseek
LLM_API_KEY=<your_llm_provider_key>
LLM_MODEL=                   # optional; defaulted per provider
LLM_URL=                     # optional base URL for OpenAI-compatible providers (deepseek)
ALLOWED_ORIGINS=https://careera.vercel.app
```

**Frontend (Vercel):**
```env
NEXT_PUBLIC_API_URL=https://careera-api.onrender.com/api/v1
```

---

## 3. Advanced: Docker & VPS Deployment

If the project outgrows the free tiers or requires a dedicated Virtual Private Server (VPS like AWS EC2, DigitalOcean), the codebase is fully container-ready. 

*(Note: VPS hosting is rarely free long-term, and requires you to manage your own Linux server, security, and reverse proxies).*

### Where to get a Free VPS for Learning
If you want to practice manual Docker/VPS deployments (which is great for learning DevOps), here are the best free options:
*   **Oracle Cloud (Always Free):** The most generous free tier. Gives you up to 4 ARM Ampere A1 instances with 24GB of RAM. *Highly recommended for running full Docker Compose stacks.*
*   **AWS EC2 (Free Tier):** Gives you 1 `t2.micro` or `t3.micro` instance (1GB RAM) free for 12 months.
*   **Google Cloud Platform (Always Free):** Gives you 1 `e2-micro` instance (1GB RAM, specific US regions only).

### Docker Compose
A `docker-compose.prod.yml` can be used to spin up the entire stack locally or on a VPS:

```yaml
version: '3.8'

services:
  careera-db:
    image: mongo:6.0
    volumes:
      - careera_mongo_data:/data/db

  careera-api:
    build: ./backend
    env_file: .env.production
    ports:
      - "8000:8000"
    depends_on:
      - careera-db

  careera-web:
    build: ./frontend
    env_file: .env.production
    ports:
      - "3000:3000"
    depends_on:
      - careera-api

volumes:
  careera_mongo_data:
```

### Manual CI/CD Pipeline
If using a VPS, you would need to write a GitHub Actions pipeline (e.g., `.github/workflows/deploy.yml`) that:
1. Runs tests on PRs.
2. Builds Docker images on merge to `main`.
3. Pushes images to Docker Hub.
4. SSHs into the VPS to run `docker-compose pull && docker-compose up -d`.
