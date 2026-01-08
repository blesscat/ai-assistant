from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat_router, oauth_router
from ..config import settings

app = FastAPI(
    title="AI Assistant API",
    description="AI 助理後端 API，使用 Google ADK",
    version="0.1.0",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(chat_router)
app.include_router(oauth_router)


@app.get("/")
async def root():
    return {"message": "AI Assistant API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
