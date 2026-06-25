# RAG Chat Application

A full-stack ChatGPT-like chat application with authentication, file upload, and AI-powered responses.

## Stack

- **Frontend**: Next.js 16, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, JWT authentication
- **Database**: PostgreSQL
- **Infrastructure**: Docker Compose

## Project Structure

```
/backend    - FastAPI REST API (auth, chat, file upload)
/frontend   - Next.js app with ChatGPT-like UI
/docker     - Docker Compose configuration
```

## Quick Start (Docker)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp docker/.env.example docker/.env
# Edit .env files with your secrets, then:
cd docker
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Local Development

### 1. Configure environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp docker/.env.example docker/.env
```

Set secrets in `backend/.env` (including `DATABASE_URL`), `frontend/.env`, and `docker/.env`. Do not commit `.env` files.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:3000

## Features

- **Authentication**: Sign up, log in, and log out via FastAPI JWT endpoints
- **Chat interface**: ChatGPT-style dark UI with sidebar, conversation history, and message threads
- **File upload**: Attach text/code files to messages; content is included in AI context
- **AI responses**: Set `OPENAI_API_KEY` for real GPT responses, or use built-in demo mode

## API Endpoints

### Auth
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Log in (returns JWT)
- `POST /api/auth/logout` - Log out
- `GET /api/auth/me` - Current user

### Chat
- `GET /api/chat/conversations` - List conversations
- `POST /api/chat/conversations` - Create conversation
- `GET /api/chat/conversations/{id}` - Get conversation with messages
- `DELETE /api/chat/conversations/{id}` - Delete conversation
- `POST /api/chat` - Send message and get AI response

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/{id}` - Get file metadata

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for JWT tokens |
| `CORS_ORIGINS` | Allowed frontend origins |
| `OPENAI_API_KEY` | Optional OpenAI API key |

### Frontend (`frontend/.env`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## Production Deployment (Docker)

Deploy frontend, backend, and HTTPS reverse proxy on a VPS (DigitalOcean, Hetzner, AWS EC2, etc.).

### Architecture

```text
Internet
  → Caddy (:443 HTTPS)
      → app.yourdomain.com  → frontend:3000
      → api.yourdomain.com  → backend:8000
                                    → cloud PostgreSQL
```

### 1. Server prerequisites

- Ubuntu 22.04+ (or similar Linux)
- [Docker](https://docs.docker.com/engine/install/) and Docker Compose v2
- A domain with two DNS A records pointing to the server IP:
  - `app.yourdomain.com`
  - `api.yourdomain.com`

### 2. Configure production env

On the server:

```bash
git clone <your-repo-url> rag
cd rag/docker
cp .env.production.example .env.production
nano .env.production   # set domains, DATABASE_URL, JWT_SECRET, etc.
```

Required values in `docker/.env.production`:

| Variable | Example |
|----------|---------|
| `APP_DOMAIN` | `app.yourdomain.com` |
| `API_DOMAIN` | `api.yourdomain.com` |
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com` |
| `CORS_ORIGINS` | `https://app.yourdomain.com` |
| `DATABASE_URL` | your cloud Postgres URL |
| `JWT_SECRET` | long random string |

### 3. Build and start

```bash
cd docker
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Caddy obtains TLS certificates automatically on first request.

### 4. Verify

```bash
docker compose -f docker-compose.prod.yml ps
curl https://api.yourdomain.com/health
```

Open `https://app.yourdomain.com` in your browser.

### 5. Updates

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Local Docker (development)

For local testing with exposed ports (no HTTPS):

```bash
cd docker
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
