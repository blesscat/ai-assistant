# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Turborepo monorepo containing a multimodal AI chatbot with Google Calendar integration:
- **Frontend**: Next.js 16 (App Router) with TypeScript, Tailwind CSS 4, and Radix UI
- **Backend**: Python FastAPI with Google ADK (Agent Development Kit) for multi-agent AI
- **Database**: Supabase PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Package Manager**: pnpm (frontend/root), uv (backend Python)

## Development Commands

### Root Level (Turborepo)
```bash
pnpm dev          # Start both frontend and backend in watch mode
pnpm build        # Build all apps
pnpm lint         # Lint all apps
pnpm format       # Format code with Prettier
```

### Frontend (apps/web)
```bash
cd apps/web
pnpm dev          # Next.js dev server on localhost:3000
pnpm build        # Production build
pnpm lint         # ESLint
pnpm format       # Prettier formatting
```

### Backend (apps/adk)
```bash
cd apps/adk
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000  # Dev server (or use pnpm dev from root)
uv run ruff check src                  # Lint
uv run ruff format src                 # Format
uv run alembic upgrade head            # Apply database migrations
uv run alembic revision --autogenerate -m "description"  # Generate migration
```

## Architecture Overview

### Communication Flow

```
Browser → Next.js API Route (/api/chat) → FastAPI (/api/chat) → Google ADK Runner → Gemini Models
```

**Request Flow**:
1. Frontend sends POST to `/api/chat` with messages, user_id, conversation_id
2. Next.js proxy validates NextAuth session and transforms Vercel AI SDK v6 message format
3. Backend creates Google ADK Runner with root_agent and streams SSE response
4. SSE events (`text-start`, `text-delta`, `text-end`, `finish`) proxied back to client

**Message Format Transform**:
- Frontend uses Vercel AI SDK v6 format with `parts` array
- Backend receives simple `{role, content}` format
- Response streamed as SSE with `data: {...}\n\n` format

### Multi-Agent System (Google ADK)

**Agent Hierarchy**:
- **root_agent** (Gemini 2.5 Flash Lite): Main coordinator that handles general queries and delegates specialized tasks
- **calendar_agent** (Gemini 2.0 Flash Lite): Sub-agent for Google Calendar operations

**Agent Registration**: Sub-agents are registered in the root agent's `sub_agents` list and automatically delegated to based on task requirements.

**Tool Injection Pattern**:
- `before_tool_callback`: Injects `access_token` before calendar tool calls
- `on_tool_error_callback`: Handles authorization failures gracefully
- Tools: `list_calendar_events`, `create_calendar_event`, `update_calendar_event`, `delete_calendar_event`

**System Prompts**: Stored as markdown files in `apps/adk/src/prompts/` (Traditional Chinese). Loaded at agent initialization, not hardcoded.

### Authentication Architecture

**Dual OAuth Flow**:
1. **Frontend (NextAuth.js)**: Basic identity only (email, name, google_id) via Google OAuth
2. **Backend (FastAPI)**: Separate Google Calendar OAuth flow initiated when calendar features are needed

**Why Separate?**:
- Flexible scope management for different services
- Backend controls sensitive API tokens
- Easier to add new OAuth providers without frontend changes

**Token Management**:
- `TokenService` class handles get/refresh/save operations
- Tokens stored in `user_tokens` table with automatic refresh on expiry
- Frontend only sends `user_id`, never handles OAuth tokens directly

### Database Schema

```
users
├── id (UUID, PK)
├── google_id (unique)
├── email
├── name
└── image

user_tokens
├── id (UUID, PK)
├── user_id (FK → users)
├── provider (e.g., 'google_calendar')
├── access_token (encrypted)
├── refresh_token (encrypted)
├── expires_at
└── scopes (array)

conversations
├── id (UUID, PK)
├── user_id (FK → users)
├── title
└── timestamps

messages
├── id (UUID, PK)
├── conversation_id (FK → conversations)
├── role (user/assistant/system)
├── content
├── attachments (JSONB)
└── created_at
```

**Migration Workflow**:
```bash
# After modifying models in apps/adk/src/db/models.py
cd apps/adk
uv run alembic revision --autogenerate -m "description of changes"
uv run alembic upgrade head
```

### State Management

**Frontend**:
- **Zustand** (`stores/chat-store.ts`): Chat conversations list, current conversation ID (persisted to localStorage)
- **Jotai** (`atoms/ui-atoms.ts`): Lightweight UI state (sidebar open, theme, recording status)
- **Vercel AI SDK**: Built-in message state via `useChat()` hook, handles streaming updates

### Key API Endpoints

**Chat**:
- `POST /api/chat`: SSE streaming chat endpoint (accepts messages, user_id, conversation_id)
- Frontend receives `text-delta` events and updates UI in real-time

**Conversations**:
- `GET /api/conversations?user_id=...`: List user's conversations
- `GET /api/conversations/{id}?user_id=...`: Get conversation with messages
- `POST /api/conversations`: Create new conversation
- `DELETE /api/conversations/{id}`: Delete conversation
- `PATCH /api/conversations/{id}/title`: Update conversation title

**OAuth**:
- `GET /auth/google/calendar?user_id=...`: Initiate Google Calendar OAuth
- `GET /auth/google/callback?code=...&state=user_id`: OAuth callback (exchanges code for tokens)
- `GET /auth/google/status?user_id=...`: Check if user has authorized Calendar

## Important Files

### Critical for Understanding Architecture
1. `apps/web/src/lib/auth.ts` - NextAuth configuration
2. `apps/web/src/app/api/chat/route.ts` - Chat API proxy with message format transformation
3. `apps/adk/src/api/routes/chat.py` - Backend SSE chat logic and Google ADK integration
4. `apps/adk/src/agents/root_agent.py` - Main agent definition and sub-agent registration
5. `apps/adk/src/services/token_service.py` - OAuth token management with auto-refresh
6. `apps/adk/src/db/models.py` - SQLAlchemy models and database schema

### Directory Structure Highlights

**Frontend** (`apps/web/src`):
- `app/(auth)/login/page.tsx` - Google OAuth sign-in UI
- `app/(chat)/page.tsx` - Main chat interface
- `app/api/auth/[...nextauth]/route.ts` - NextAuth handlers
- `components/chat/chat-container.tsx` - Main chat component using `useChat()` hook
- `components/chat/voice-recorder.tsx` - Web Audio API voice recording

**Backend** (`apps/adk/src`):
- `agents/` - Agent definitions (root_agent.py, calendar_agent.py)
- `prompts/` - System prompts as markdown files (Traditional Chinese)
- `tools/calendar_tools.py` - Google Calendar API wrappers
- `api/routes/` - FastAPI route handlers (chat.py, oauth.py, conversations.py)
- `db/models.py` - SQLAlchemy ORM models
- `services/token_service.py` - Token lifecycle management
- `constants.py` - Agent names, model names, OAuth scopes

## Environment Configuration

**Required Environment Variables**:

Frontend (`.env.local` or `.env`):
```bash
GOOGLE_CLIENT_ID=...           # Google Cloud Console OAuth client
GOOGLE_CLIENT_SECRET=...       # Google Cloud Console OAuth client
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=...            # Generate: openssl rand -base64 32
ADK_API_URL=http://localhost:8000
```

Backend (`.env`):
```bash
GOOGLE_CLIENT_ID=...           # Same as frontend
GOOGLE_CLIENT_SECRET=...       # Same as frontend
GOOGLE_GENERATIVE_AI_API_KEY=...  # Google AI Studio API key
SUPABASE_URL=https://...       # Supabase project URL
SUPABASE_KEY=...               # Supabase service role key
DATABASE_URL=postgresql://...  # Supabase database connection string
ENCRYPTION_KEY=...             # Base64 key for token encryption
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

**Setup**: Copy `.env.example` files from `apps/web/.env.example` and `apps/adk/.env.example` and fill in values.

## Common Development Patterns

### Adding a New Agent

1. Create agent file in `apps/adk/src/agents/new_agent.py`
2. Create prompt file in `apps/adk/src/prompts/new_agent.md` (Traditional Chinese)
3. Define tools in `apps/adk/src/tools/` if needed
4. Register in root agent's `sub_agents` list
5. Update `apps/adk/src/constants.py` with agent name constant

### Adding a New API Endpoint

1. Create route file in `apps/adk/src/api/routes/`
2. Import and include router in `apps/adk/src/api/main.py`
3. Add frontend proxy in `apps/web/src/app/api/` if needed

### Modifying Database Schema

1. Edit models in `apps/adk/src/db/models.py`
2. Generate migration: `cd apps/adk && uv run alembic revision --autogenerate -m "description"`
3. Review generated migration in `apps/adk/src/migrations/versions/`
4. Apply: `uv run alembic upgrade head`

## Technology Stack Details

**Frontend Dependencies**:
- `next` 16.1.1 - App Router with Server Components
- `react` 19.2.3 - Latest React with new features
- `next-auth` 5.0.0-beta.30 - Authentication with Google OAuth
- `ai` 6.0.19 + `@ai-sdk/react` - Vercel AI SDK for streaming chat
- `zustand` 5.0.9 - Client state management
- `jotai` 2.16.1 - Atomic state management
- `@radix-ui/*` - Unstyled accessible UI components
- `tailwindcss` 4 - Utility-first CSS

**Backend Dependencies**:
- `fastapi` 0.128+ - Modern async Python web framework
- `google-adk` - Google Agent Development Kit for multi-agent AI
- `sqlalchemy` 2.0+ - Async-capable ORM
- `alembic` - Database migrations
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variable loading

**Build Tools**:
- `turbo` 2.3.0 - Monorepo task orchestration
- `pnpm` 9.15.0 - Fast package manager with workspaces
- `uv` - Fast Python package manager

## Notes

- **Language**: System prompts and agent instructions are in Traditional Chinese (`繁體中文`)
- **Timezone**: Default timezone is `Asia/Taipei` for calendar operations
- **UUID Handling**: Backend accepts both UUID format and google_id for user identification
- **SSE Format**: SSE events must be compatible with Vercel AI SDK v6 streaming protocol
- **Node Version**: Requires Node.js >= 18
- **Python Version**: Requires Python >= 3.12
