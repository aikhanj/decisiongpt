# Gentleman Coach

A web application that helps users make romantic relationship decisions via guided questions and curated options. It acts as a coach (not a therapist), driving toward action with clear options, scripts, and execution plans.

## Core Philosophy

- **Coach, not therapist**: Drives toward action, not emotional processing
- **Human in the loop**: Never outputs a single final decision; always offers 2-3 moves for the user to choose
- **Gentleman Mode**: All suggestions follow principles of respect, clarity, and confident leadership
- **No manipulation**: Hard guardrails against guilt tactics, persistence after rejection, negging, or deception

## Features

- **Two-Phase AI System**:
  - Phase 1 (Clarify): Generates 5-15 specific questions based on the situation
  - Phase 2 (Moves): Produces 2-3 actionable options with scripts and branches
- **Situation Templates**: Specialized guidance for gym approaches, double texts, kiss timing, and first date planning
- **Mood Detection**: Flags anxious/tired/horny states and recommends cool-down periods
- **Branching**: Explore alternative paths when situations evolve
- **Calibration**: Brier score tracking for probability calibration over time
- **Optional Semantic Memory**: Store and retrieve similar past situations via pgvector
- **BYOK (Bring Your Own Key)**: Users provide their own OpenAI API key

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Framer Motion
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic
- **Database**: PostgreSQL + pgvector extension
- **AI**: OpenAI GPT-4o (BYOK - user provides API key)
- **Infrastructure**: Docker Compose

## BYOK (Bring Your Own Key)

This application uses a **Bring Your Own Key** model for OpenAI API access:

- **No server-side API key**: Users must provide their own OpenAI API key
- **Local storage**: Your API key is stored in your browser's localStorage
- **Direct to OpenAI**: Your key is sent directly to OpenAI via the backend - we never store it
- **Per-request**: The key is included in each API request that requires AI

### Getting an API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the key (starts with `sk-`)
5. Enter it in the app when prompted

### Security Notes

- Your API key is stored only in your browser's localStorage
- The key is transmitted to the backend over HTTPS
- The backend sends it to OpenAI and discards it - no logging or storage
- Clear your browser data to remove the key

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

## API Walkthrough

All AI-powered endpoints require the `X-OpenAI-Key` header with your OpenAI API key.

### Create a Decision (Phase 1)

```bash
curl -X POST http://localhost:8000/api/decisions \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{
    "situation_text": "There is a woman I see at the gym 3 times a week. We have made eye contact a few times and she smiled once. I want to approach her but I am not sure how."
  }'
```

Response includes questions to answer.

### Submit Answers (Phase 2)

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/answer \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{
    "answers": [
      {"question_id": "q1", "value": false},
      {"question_id": "q2", "value": true},
      {"question_id": "q3", "value": "Just finished"}
    ]
  }'
```

Response includes 2-3 move options with scripts.

### Choose a Move

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/choose \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-your-api-key" \
  -d '{"move_id": "A"}'
```

Response includes execution plan with steps and scripts.

### Log Outcome

```bash
curl -X POST http://localhost:8000/api/decisions/{decision_id}/nodes/{node_id}/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "progress_yesno": true,
    "sentiment_2h": 1,
    "notes": "She said yes to coffee!"
  }'
```

Note: The resolve endpoint doesn't require an API key unless vector memory is enabled.

## UX Design

### Coach Interaction Model

1. **Input**: User describes their romantic situation
2. **Clarify**: System generates specific questions with tooltips explaining why each matters
3. **Options**: System presents 2-3 moves, each with:
   - Gentleman score (0-100)
   - Risk level
   - Probability of progress
   - Two script variants (direct and softer)
   - Branch responses for warm/neutral/cold reactions
4. **Execute**: User picks a move and gets a concrete checklist
5. **Track**: User logs outcome for calibration

### Key UI Elements

- **Gentleman Mode Badge**: Always visible, indicates respectful guidelines active
- **API Key Status**: Shows whether your OpenAI key is configured
- **Cool-down Banner**: Appears when mood suggests waiting
- **Tooltips**: Every question has "Why I'm asking" and "What it changes" tooltips
- **Script Copy**: One-click copy for message scripts

## Guardrails

### Hard Reject Patterns

These patterns will never appear in recommendations:

- Persistence after rejection
- Jealousy manipulation ("make her jealous")
- Negging or backhanded compliments
- Lying or deception
- Guilt-tripping
- Sexual escalation without clear signals
- Wall-of-text messages (>200 words)

### Cool-down Triggers

When detected, system recommends waiting:

- Mood states: anxious, tired, horny, angry
- Late night timing (23:00-06:00)
- Recent rejection (within 24h)

## Feature Flags

### USE_VECTOR_MEMORY

Set `USE_VECTOR_MEMORY=true` to enable semantic memory:

- Stores decision summaries with embeddings
- Retrieves similar past situations
- Shows "Past patterns" cards in UI
- Requires API key to be provided when resolving outcomes

Requires OpenAI embedding model (`text-embedding-ada-002`).

## Running Tests

```bash
# Run all tests
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest app/tests/test_guardrails.py

# Run with coverage
docker compose exec backend pytest --cov=app
```

## Project Structure

```
decisiongpt/
├── docker-compose.yml
├── .env.example
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   │   ├── settings/    # API key management
│   │   │   └── ...
│   │   ├── lib/             # Utilities and API client
│   │   └── types/           # TypeScript types
│   └── package.json
└── backend/                  # FastAPI backend
    ├── app/
    │   ├── ai/              # AI gateway and prompts
    │   ├── dependencies.py  # API key extraction
    │   ├── guardrails/      # Guardrail checker
    │   ├── models/          # SQLAlchemy models
    │   ├── routers/         # API endpoints
    │   ├── schemas/         # Pydantic schemas
    │   ├── services/        # Business logic
    │   ├── templates/       # Situation templates
    │   └── tests/           # Unit tests
    ├── alembic/             # Database migrations
    └── pyproject.toml
```

## Assumptions

1. **Auth**: Stub user system with single default user. Tables are ready for future auth implementation.
2. **AI Provider**: OpenAI GPT-4o only (BYOK). No alternative providers implemented.
3. **Embedding Model**: OpenAI text-embedding-ada-002 (1536 dimensions).
4. **Calibration**: v1 uses raw probabilities. Binning calibration is stubbed for future implementation.
5. **Demo User**: UUID `00000000-0000-0000-0000-000000000001` for seed data.

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

## License

Private - All rights reserved.
