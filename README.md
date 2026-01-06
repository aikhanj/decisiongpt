# Decision Canvas

A web application that helps users make better decisions through AI-powered structured thinking. It features a hybrid Chat + Canvas UX where conversation flows on the left and a structured decision canvas updates in real-time on the right.

## Core Philosophy

- **Structure over chaos**: Breaks down complex decisions into clear components
- **Human in the loop**: Never outputs a single final decision; always offers 2-3 options for the user to choose
- **Actionable outcomes**: Every decision ends with a concrete commit plan with steps and contingencies
- **Learning from outcomes**: Track results to improve decision-making over time

## Features

- **Hybrid Chat + Canvas UX**: Split-pane interface with conversational AI on the left and structured canvas on the right
- **Three-Phase Flow**:
  - Phase 1 (Clarify): AI asks questions to understand your situation, constraints, and criteria
  - Phase 2 (Options): AI generates 2-3 distinct options with pros, cons, risks, and confidence levels
  - Phase 3 (Execute): After choosing, get a detailed commit plan with steps and if-then contingencies
- **Decision Branching**: Create alternative paths when circumstances change (DAG structure)
- **Real-time Canvas**: Watch your decision canvas populate as you chat
- **Outcome Tracking**: Log results with sentiment tracking and Brier score calibration
- **7 Canvas Tabs**: Summary, Options, Criteria, Constraints, Risks, Outcome, History
- **BYOK (Bring Your Own Key)**: Users provide their own OpenAI API key

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Framer Motion
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic
- **Database**: PostgreSQL + pgvector extension
- **AI**: OpenAI GPT-4o (BYOK - user provides API key)
- **Infrastructure**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd decisiongpt
```

2. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env if needed (database settings, etc.)
```

3. Start the services:
```bash
docker compose up -d
```

4. Run database migrations:
```bash
docker compose exec backend alembic upgrade head
```

5. (Optional) Seed demo data:
```bash
docker compose exec backend python seed_data.py
```

6. Access the app:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

7. Enter your OpenAI API key when prompted in the app

## Development Setup (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"

# Start PostgreSQL (via Docker or local install)
# Set DATABASE_URL environment variable

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Walkthrough

All AI-powered endpoints require the `X-OpenAI-Key` header with your OpenAI API key.

### Start a New Decision

```bash
curl -X POST http://localhost:8000/api/decisions \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{
    "situation_text": "I need to decide whether to accept a job offer at a startup. The salary is 20% higher but it requires relocating, and my current company has good work-life balance."
  }'
```

### Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/chat \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{
    "message": "I value stability but also want career growth. The startup is well-funded."
  }'
```

### Choose an Option

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/choose \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{"option_id": "A"}'
```

### Log Outcome

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "progress_yesno": true,
    "sentiment_2h": 1,
    "sentiment_24h": 2,
    "notes": "Made the move and it worked out great!"
  }'
```

## Project Structure

```
decisiongpt/
├── docker-compose.yml
├── .env.example
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # App router pages
│   │   │   ├── page.tsx     # Home page
│   │   │   └── d/
│   │   │       ├── new/     # New decision page
│   │   │       └── [id]/    # Decision workspace
│   │   ├── components/
│   │   │   ├── chat/        # Chat panel components
│   │   │   ├── canvas/      # Canvas container and tabs
│   │   │   ├── layout/      # Split pane, header
│   │   │   ├── clarify/     # Question cards
│   │   │   ├── commit/      # Commit plan view
│   │   │   ├── branching/   # Branch modal and indicator
│   │   │   └── ui/          # shadcn/ui components
│   │   ├── lib/             # Utilities and API client
│   │   └── types/           # TypeScript types
│   └── package.json
└── backend/                  # FastAPI backend
    ├── app/
    │   ├── ai/              # AI gateway and prompts
    │   │   └── prompts/     # System, phase1, phase2 prompts
    │   ├── models/          # SQLAlchemy models
    │   ├── routers/         # API endpoints (chat.py, decisions.py)
    │   ├── schemas/         # Pydantic schemas (canvas.py, decision.py)
    │   ├── services/        # Business logic (chat_service.py)
    │   └── tests/           # Unit tests
    ├── alembic/             # Database migrations
    └── pyproject.toml
```

## Canvas Tabs

1. **Summary**: Decision statement, context bullets, quick stats
2. **Options**: 2-3 option cards with pros/cons, risks, confidence levels
3. **Criteria**: Weighted evaluation criteria (1-10 scale)
4. **Constraints**: Hard constraints (must have) and soft constraints (nice to have)
5. **Risks**: Risk assessment across all options
6. **Outcome**: Log decision results with sentiment tracking
7. **History**: Decision tree visualization with branching

## BYOK (Bring Your Own Key)

This application uses a **Bring Your Own Key** model for OpenAI API access:

- **No server-side API key**: Users must provide their own OpenAI API key
- **Local storage**: Your API key is stored in your browser's localStorage
- **Direct to OpenAI**: Your key is sent to OpenAI via the backend - we never store it
- **Per-request**: The key is included in each API request that requires AI

### Getting an API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the key (starts with `sk-`)
5. Enter it in the app when prompted

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model name | `text-embedding-ada-002` |
| `USE_VECTOR_MEMORY` | Enable semantic memory | `false` |
| `POSTGRES_USER` | Database user | `gentleman` |
| `POSTGRES_PASSWORD` | Database password | `gentleman_secret` |
| `POSTGRES_DB` | Database name | `gentleman_coach` |

Note: OpenAI API key is provided by users via the `X-OpenAI-Key` header, not configured server-side.

## Running Tests

```bash
# Run all tests
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest app/tests/test_guardrails.py

# Run with coverage
docker compose exec backend pytest --cov=app
```

## License

Private - All rights reserved.
