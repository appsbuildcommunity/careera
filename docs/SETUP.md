# ⚙️ Setup Guide

Everything you need to get Careera running locally for development.

---

## Prerequisites

```bash
node --version    # v18+
python --version  # v3.11+
docker --version  # Recommended for MongoDB
```

Missing anything? [Node.js](https://nodejs.org/) | [Python](https://www.python.org/) | [Docker](https://www.docker.com/)

---

## Project Structure (Quick View)

```
careera/
├── frontend/          # Next.js app — Port 3000
├── backend/           # FastAPI app — Port 8000
└── docker-compose.yml # MongoDB container
```

Full structure breakdown is in [TECH_SPECS.md](./TECH_SPECS.md#project-structure).

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/appsbuild/careera.git
cd careera
```

---

## Step 2 — Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env            # Then fill in your credentials (see below)
```

**`backend/.env` variables:**

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
DB_NAME=careera_db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AI provider
# Use the API key variable expected by the currently configured provider
AI_PROVIDER_API_KEY=your-ai-provider-api-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

**Start the backend:**

```bash
uvicorn app.main:app --reload --port 8000
```

Visit [http://localhost:8000](http://localhost:8000) — you should see `{"message":"Careera API is running"}`.
Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Step 3 — MongoDB

**Option A: Docker (recommended)**

Use the existing [docker-compose.yml](../docker-compose.yml) in the project root:

```bash
docker-compose up -d       # Start
docker-compose down        # Stop
docker-compose logs -f     # View logs
```

Update `MONGODB_URI` in `backend/.env`:

```env
MONGODB_URI=mongodb://localhost:27017
```

**Option B: Local install**

Download from [mongodb.com](https://www.mongodb.com/try/download/community).

---

## Step 4 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

**`frontend/.env.local` variables:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Start the frontend:**

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).

---

## Step 5 — Get Credentials

**Google OAuth** (for user login)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Google+ API**
4. Create an **OAuth 2.0 Client ID** (Web application)
5. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
6. Copy the **Client ID** and **Client Secret** into `backend/.env`

**AI provider API key** (for AI-powered features)

1. Use the provider you want for AI features.
2. Create an API key from that provider.
3. Add it to `backend/.env` using the environment variable expected by your current backend configuration.

---

## Verification Checklist

```bash
# Backend
curl http://localhost:8000
# → {"message":"Careera API is running","version":"1.0.0"}

# MongoDB (if using Docker)
docker ps
# → Should show careera-mongo container running

# Frontend
# → Open http://localhost:3000 in your browser
```

---

## Daily Development Workflow

```bash
# Terminal 1 — MongoDB
docker-compose up -d

# Terminal 2 — Backend
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm run dev
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push and open a Pull Request

Please follow the existing code structure and keep PRs focused. For technical context, refer to [TECH_SPECS.md](./TECH_SPECS.md).