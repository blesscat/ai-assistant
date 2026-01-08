# AI Assistant - Turborepo Monorepo 實作計劃

## 專案概述
建立一個 Turborepo monorepo，包含 Next.js 前端和 Python (Google ADK) 後端的多模態 AI Chatbot，支援 Google Calendar 整合。

## 技術棧

### 前端 (apps/web)
- **Framework**: Next.js 14+ (App Router)
- **Auth**: NextAuth.js + Google OAuth (Calendar scope)
- **UI**: Radix UI, Lucide React
- **State**: Zustand, Jotai
- **Chat**: Vercel AI SDK (`useChat`)
- **Streaming**: SSE (Server-Sent Events)

### 後端 (apps/adk)
- **Framework**: FastAPI + Google ADK
- **Package Manager**: uv
- **ORM**: SQLAlchemy (Supabase PostgreSQL)
- **Migration**: Alembic
- **Models**:
  - 主 Agent: gemini-2.5-flash-lite
  - SubAgent: gemini-2.0-flash-lite
- **Architecture**: Multi-Agent (主 Agent + Calendar SubAgent)

### 已有配置 (.env)
- Google OAuth Client ID/Secret
- Supabase URL/Key/DB credentials
- NextAuth Secret

---

## 專案結構

```
ai-assistant/
├── apps/
│   ├── web/                          # Next.js 前端
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── (chat)/
│   │   │   │   ├── page.tsx          # 主聊天頁面
│   │   │   │   └── layout.tsx
│   │   │   ├── api/
│   │   │   │   ├── auth/[...nextauth]/route.ts
│   │   │   │   └── chat/route.ts     # Proxy to Python backend
│   │   │   ├── layout.tsx
│   │   │   └── providers.tsx
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── chat-container.tsx
│   │   │   │   ├── message-list.tsx
│   │   │   │   ├── message-item.tsx
│   │   │   │   ├── chat-input.tsx
│   │   │   │   ├── file-upload.tsx
│   │   │   │   └── voice-recorder.tsx
│   │   │   └── ui/                   # Radix UI wrappers
│   │   ├── lib/
│   │   │   ├── auth.ts               # NextAuth config
│   │   │   └── utils.ts
│   │   ├── stores/
│   │   │   └── chat-store.ts         # Zustand store
│   │   └── atoms/
│   │       └── ui-atoms.ts           # Jotai atoms
│   │
│   └── adk/                          # Python 後端 (Google ADK)
│       ├── src/
│       │   ├── constants.py          # Agent names, model names
│       │   ├── agents/
│       │   │   ├── __init__.py
│       │   │   ├── root_agent.py     # 主 Agent (gemini-2.5-flash-lite)
│       │   │   └── calendar_agent.py # Calendar SubAgent (gemini-2.0-flash-lite)
│       │   ├── prompts/              # Agent instructions (繁體中文)
│       │   │   ├── root_agent.md     # 主 Agent 指令
│       │   │   └── calendar_agent.md # Calendar Agent 指令
│       │   ├── tools/
│       │   │   ├── __init__.py
│       │   │   └── calendar_tools.py # Calendar CRUD tools
│       │   ├── db/
│       │   │   ├── __init__.py
│       │   │   ├── base.py           # SQLAlchemy base
│       │   │   ├── models.py         # User, UserToken, Conversation, Message
│       │   │   └── session.py        # DB session management
│       │   ├── migrations/           # Alembic migrations
│       │   │   ├── versions/         # Migration scripts
│       │   │   ├── env.py
│       │   │   └── script.py.mako
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── main.py           # FastAPI app
│       │   │   └── routes/
│       │   │       ├── __init__.py
│       │   │       ├── chat.py       # SSE chat endpoint
│       │   │       └── oauth.py      # Google Calendar OAuth endpoints
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   └── token_service.py  # Token 管理 (取得/刷新)
│       │   └── config.py
│       ├── alembic.ini               # Alembic config
│       ├── pyproject.toml            # uv project config
│       └── uv.lock
│
├── packages/                         # 共享套件 (可選)
│   └── shared-types/
│
├── turbo.json
├── package.json
├── pnpm-workspace.yaml
├── PLAN.md                           # 本文件
└── .env
```

---

## 實作步驟

### Phase 1: Turborepo 基礎架構設置 ✅

- [x] 1. **初始化 Turborepo monorepo**
  ```bash
  pnpm dlx create-turbo@latest . --skip-install
  ```

- [x] 2. **配置 pnpm-workspace.yaml**
  ```yaml
  packages:
    - "apps/*"
    - "packages/*"
  ```

- [x] 3. **配置 turbo.json**
  - 定義 `build`, `dev`, `lint` tasks
  - 設置 Next.js 和 Python app 的 outputs

### Phase 2: Next.js 前端 (apps/web) ✅

- [x] 1. **建立 Next.js app**
  ```bash
  pnpm dlx create-next-app@latest apps/web --typescript --tailwind --app
  ```

- [x] 2. **安裝依賴**
  ```bash
  pnpm add next-auth @auth/core
  pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-avatar @radix-ui/react-scroll-area
  pnpm add zustand jotai
  pnpm add lucide-react
  pnpm add @ai-sdk/react ai
  ```

- [x] 3. **NextAuth.js + Google OAuth 設置**
  - 配置 Google Provider
  - 只做基本登入 (email, name, google_id)
  - Calendar 授權由後端處理

- [x] 4. **Chat UI 組件**
  - `ChatContainer`: 主容器，使用 `useChat` hook
  - `MessageList`: 訊息列表 (Radix ScrollArea)
  - `MessageItem`: 單一訊息 (支援 text, image 顯示)
  - `ChatInput`: 輸入框 + 發送按鈕
  - `FileUpload`: 圖片上傳 (支援拖放)
  - `VoiceRecorder`: 語音錄製 (Web Audio API → 轉文字)

- [x] 5. **狀態管理**
  - Zustand: 聊天歷史、當前對話
  - Jotai: UI 狀態 (sidebar open, theme 等)

- [x] 6. **API Route (Proxy)**
  - `/api/chat/route.ts`: 轉發請求到 Python 後端

### Phase 3: Python 後端 (apps/adk) ✅

- [x] 1. **專案初始化 (使用 uv)**
  ```bash
  mkdir -p apps/adk
  cd apps/adk
  uv init
  uv add google-adk fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv google-auth google-api-python-client sse-starlette
  ```

- [x] 2. **Constants 檔案 (src/constants.py)**
  ```python
  # Agent Names
  ROOT_AGENT_NAME = "assistant"
  CALENDAR_AGENT_NAME = "calendar_agent"

  # Model Names
  ROOT_AGENT_MODEL = "gemini-2.5-flash-lite"
  SUB_AGENT_MODEL = "gemini-2.0-flash-lite"

  # Prompt Paths
  PROMPTS_DIR = "src/prompts"
  ```

- [x] 3. **Prompt 檔案 (繁體中文)**

  **src/prompts/root_agent.md**:
  ```markdown
  你是一個智慧助理，專門協助台灣使用者處理日常任務。

  ## 你的職責
  - 回答使用者的一般問題
  - 當使用者詢問行事曆相關事項時，將任務委派給 calendar_agent

  ## 委派規則
  - 查詢、新增、修改、刪除行事曆事件 → 委派給 calendar_agent
  - 其他問題 → 直接回答

  ## 回應風格
  - 使用繁體中文回應
  - 語氣友善、專業
  - 回答簡潔明瞭
  ```

  **src/prompts/calendar_agent.md**:
  ```markdown
  你是行事曆管理專家，負責管理使用者的 Google 日曆。

  ## 你的職責
  - 查詢行事曆事件
  - 新增行事曆事件
  - 修改現有事件
  - 刪除事件

  ## 工具使用指南
  - list_calendar_events: 查詢指定時間範圍內的事件
  - create_calendar_event: 新增事件（需要標題、開始/結束時間）
  - update_calendar_event: 修改現有事件
  - delete_calendar_event: 刪除事件

  ## 注意事項
  - 時間格式使用 ISO 8601
  - 預設時區為 Asia/Taipei
  - 新增事件前確認使用者提供了必要資訊
  ```

- [x] 4. **SQLAlchemy Models (src/db/models.py)**
  - `User`: id, google_id, email, name, created_at, updated_at
  - `UserToken`: id, user_id, provider, access_token, refresh_token, expires_at, scopes
  - `Conversation`: id, user_id, title, created_at, updated_at
  - `Message`: id, conversation_id, role, content, attachments, created_at

- [x] 5. **Alembic 設置**
  ```bash
  cd apps/adk
  alembic init src/migrations
  ```

  **alembic.ini** (關鍵設定):
  ```ini
  script_location = src/migrations
  sqlalchemy.url = postgresql://...  # 從環境變數讀取
  ```

  **src/migrations/env.py** (關鍵修改):
  ```python
  from src.db.base import Base
  from src.db.models import User, UserToken, Conversation, Message

  target_metadata = Base.metadata

  # 從環境變數讀取 DATABASE_URL
  config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
  ```

  **常用指令**:
  ```bash
  # 產生 migration
  alembic revision --autogenerate -m "create initial tables"

  # 執行 migration
  alembic upgrade head

  # 回滾
  alembic downgrade -1
  ```

- [x] 6. **Google ADK Agents**

  **Root Agent (src/agents/root_agent.py)**:
  ```python
  from pathlib import Path
  from google.adk import Agent
  from ..constants import ROOT_AGENT_NAME, ROOT_AGENT_MODEL, PROMPTS_DIR
  from .calendar_agent import calendar_agent

  def load_instruction(filename: str) -> str:
      path = Path(PROMPTS_DIR) / filename
      return path.read_text(encoding="utf-8")

  root_agent = Agent(
      name=ROOT_AGENT_NAME,
      model=ROOT_AGENT_MODEL,
      description="主要助理，負責協調任務分配",
      instruction=load_instruction("root_agent.md"),
      sub_agents=[calendar_agent]
  )
  ```

  **Calendar Agent (src/agents/calendar_agent.py)**:
  ```python
  from pathlib import Path
  from google.adk import Agent
  from ..constants import CALENDAR_AGENT_NAME, SUB_AGENT_MODEL, PROMPTS_DIR
  from ..tools.calendar_tools import (
      list_calendar_events,
      create_calendar_event,
      update_calendar_event,
      delete_calendar_event
  )

  def load_instruction(filename: str) -> str:
      path = Path(PROMPTS_DIR) / filename
      return path.read_text(encoding="utf-8")

  calendar_agent = Agent(
      name=CALENDAR_AGENT_NAME,
      model=SUB_AGENT_MODEL,
      description="行事曆管理 Agent，處理 Google Calendar 操作",
      instruction=load_instruction("calendar_agent.md"),
      tools=[
          list_calendar_events,
          create_calendar_event,
          update_calendar_event,
          delete_calendar_event
      ]
  )
  ```

- [x] 7. **Calendar Tools (src/tools/calendar_tools.py)**
  - `list_calendar_events(access_token, time_min, time_max)`
  - `create_calendar_event(access_token, summary, start, end, description)`
  - `update_calendar_event(access_token, event_id, ...)`
  - `delete_calendar_event(access_token, event_id)`

- [x] 8. **FastAPI Chat Endpoint (src/api/routes/chat.py)**
  - `POST /api/chat`: SSE streaming chat endpoint
  - 接收: `{ messages, user_id, attachments }`
  - 返回: SSE stream (compatible with Vercel AI SDK)

- [x] 9. **OAuth Endpoints (src/api/routes/oauth.py)**
  ```python
  # GET /auth/google/calendar
  # - 產生 Google OAuth URL (含 Calendar scope)
  # - 重導使用者到 Google 授權頁面

  # GET /auth/google/callback
  # - 接收 auth code
  # - 換取 access_token / refresh_token
  # - 儲存到 user_tokens 表
  # - 重導回前端

  # GET /auth/google/status
  # - 檢查用戶是否已授權 Calendar
  ```

- [x] 10. **Token Service (src/services/token_service.py)**
  ```python
  class TokenService:
      async def get_valid_token(self, user_id: str, provider: str) -> str:
          """取得有效的 access_token，過期自動刷新"""

      async def refresh_token(self, user_token: UserToken) -> str:
          """使用 refresh_token 換取新的 access_token"""

      async def save_tokens(self, user_id: str, provider: str, tokens: dict):
          """儲存 OAuth tokens"""

      async def revoke_token(self, user_id: str, provider: str):
          """撤銷授權"""
  ```

### Phase 4: 整合與測試 ✅

- [x] 1. **環境變數配置**
  - 複製現有 .env 到各 app
  - 添加後端 URL 配置

- [x] 2. **Turbo 開發命令**
  ```bash
  turbo dev  # 同時啟動前後端
  ```

- [ ] 3. **測試流程** (手動測試)
  - Google OAuth 登入
  - 文字對話
  - 圖片上傳對話
  - 語音輸入 (STT)
  - Calendar 操作測試

---

## 關鍵檔案清單

### 前端 (apps/web)
- `app/api/auth/[...nextauth]/route.ts` - NextAuth 配置
- `app/api/chat/route.ts` - Chat API proxy
- `app/(chat)/page.tsx` - 主聊天頁面
- `components/chat/chat-container.tsx` - Chat UI 主組件
- `lib/auth.ts` - Auth 配置與 token 管理

### 後端 (apps/adk)
- `src/constants.py` - Agent/Model 名稱常數
- `src/prompts/root_agent.md` - 主 Agent 指令 (繁體中文)
- `src/prompts/calendar_agent.md` - Calendar Agent 指令 (繁體中文)
- `src/api/main.py` - FastAPI 入口
- `src/api/routes/chat.py` - SSE chat endpoint
- `src/api/routes/oauth.py` - Google Calendar OAuth 端點
- `src/services/token_service.py` - Token 管理服務
- `src/agents/root_agent.py` - 主 Agent
- `src/agents/calendar_agent.py` - Calendar SubAgent
- `src/tools/calendar_tools.py` - Calendar API tools
- `src/db/models.py` - SQLAlchemy models (含 UserToken)
- `src/migrations/env.py` - Alembic 環境配置
- `alembic.ini` - Alembic 設定檔
- `pyproject.toml` - uv 專案配置

---

## OAuth 架構（方案 C：後端獨立 OAuth）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐
│   Browser   │────▶│  Next.js    │────▶│  Python ADK │────▶│ Supabase │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────┘
      │                   │                    │                  │
      │ 1. Basic Login    │                    │                  │
      │   (email/name)    │                    │                  │
      │◀─────────────────▶│                    │                  │
      │                   │                    │                  │
      │ 2. Need Calendar? │                    │                  │
      │   Redirect to     │                    │                  │
      │   backend OAuth   │───────────────────▶│                  │
      │◀──────────────────────────────────────│                  │
      │                   │                    │                  │
      │ 3. User authorizes│                    │                  │
      │   Google Calendar │                    │                  │
      │──────────────────────────────────────▶│                  │
      │                   │                    │                  │
      │                   │                    │ 4. Exchange code │
      │                   │                    │    Store tokens  │
      │                   │                    │─────────────────▶│
      │                   │                    │                  │
      │ 5. Chat request   │                    │ 6. Get token     │
      │   (user_id only)  │───────────────────▶│    from DB       │
      │                   │                    │◀─────────────────│
```

### OAuth 流程說明

1. **前端 (NextAuth)**: 只做基本登入，取得 user identity (email, name, google_id)
2. **Calendar 授權**: 當用戶首次需要 Calendar 功能時，導向後端的 OAuth 端點
3. **後端 OAuth**:
   - `GET /auth/google/calendar` - 產生 Google OAuth URL，導向用戶授權
   - `GET /auth/google/callback` - 接收 auth code，換取 tokens，存入 Supabase
4. **Token 儲存**: `access_token`, `refresh_token`, `expires_at` 存在 Supabase `user_tokens` 表
5. **使用 Token**: 後端需要時從 DB 讀取，過期自動 refresh

### 新增資料表

```sql
-- user_tokens 表 (由 Alembic migration 建立)
CREATE TABLE user_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL DEFAULT 'google_calendar',
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMP WITH TIME ZONE,
  scopes TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, provider)
);
```

---

## 注意事項

1. **OAuth 分離**: 前端 NextAuth 只做身份驗證，Calendar scope 由後端獨立處理

2. **SSE 格式**: 後端 SSE 輸出需符合 Vercel AI SDK 的 stream protocol

3. **語音處理**: 使用 Web Speech API 或 Whisper API 做 STT，轉成文字後發送

4. **圖片處理**: Base64 或上傳到 Supabase Storage，傳遞 URL 給後端

5. **Token 安全**: access_token 只存在後端，前端只傳 user_id
