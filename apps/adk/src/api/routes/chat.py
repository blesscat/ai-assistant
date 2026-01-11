import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from google.adk import Runner
from google.genai import types

from ...db.session import get_db
from ...db.models import User
from ...agents.root_agent import root_agent
from ...services.token_service import TokenService
from ...services.session_service import get_session_service


router = APIRouter(prefix="/api", tags=["chat"])


class MessagePart(BaseModel):
    type: str
    text: Optional[str] = None
    data: Optional[str] = None
    mediaType: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str
    parts: Optional[List[MessagePart]] = None


class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """SSE streaming chat endpoint"""
    print(f"[DEBUG] Received request: user_id={request.user_id}, messages count={len(request.messages)}")
    if request.messages:
        print(f"[DEBUG] Last message: {request.messages[-1]}")

    async def generate():
        try:
            print("[DEBUG] Starting generate()")

            # 查詢用戶資訊
            user = None
            if request.user_id:
                try:
                    # 嘗試將 user_id 轉換為 UUID
                    import uuid as uuid_lib
                    user_uuid = uuid_lib.UUID(request.user_id)
                    user = db.query(User).filter(User.id == user_uuid).first()
                except ValueError:
                    # 如果不是 UUID 格式，可能是 google_id
                    user = db.query(User).filter(User.google_id == request.user_id).first()

                if user:
                    print(f"[DEBUG] Found user: {user.name} ({user.email})")
                else:
                    print(f"[DEBUG] User not found for user_id: {request.user_id}")

            # 使用全局 session service，避免每次創建新的
            session_service = get_session_service()

            # 建立 Runner (API key 已在 root_agent.py 中設定為環境變數)
            runner = Runner(
                app_name="agents",
                agent=root_agent,
                session_service=session_service,
            )
            print("[DEBUG] Runner created")

            # 使用 conversation_id 作為 session_id，確保同一個對話共用同一個 session
            user_id = request.user_id or "anonymous"
            session_id = request.conversation_id or str(uuid.uuid4())
            print(f"[DEBUG] Using session_id={session_id} (from conversation_id)")

            # 判斷是否為新對話（第一則訊息）
            is_new_conversation = len(request.messages) == 1

            # 檢查 session 是否已存在
            try:
                existing_session = await session_service.get_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id,
                )
                print(f"[DEBUG] Existing session found: {existing_session is not None}")
            except:
                existing_session = None
                print("[DEBUG] No existing session, will create new one")

            # 如果是新 session，創建並注入用戶資訊
            if not existing_session:
                session = await session_service.create_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id,
                )
                print(f"[DEBUG] New session created: {session}")

            # 取得最後一則訊息（當前用戶輸入）
            last_message = request.messages[-1] if request.messages else None
            if not last_message:
                yield 'data: {"type":"error","error":"No message provided"}\n\n'
                return

            # 建立當前訊息內容
            user_text = last_message.content

            # 如果是新對話且有用戶資訊，注入用戶資訊
            if is_new_conversation and user:
                user_text = f"[系統資訊] 當前用戶：{user.name}（{user.email}）\n\n{user_text}"
                print(f"[DEBUG] Injected user context for {user.name}")

            content = types.Content(
                role="user",
                parts=[types.Part(text=user_text)],
            )
            print(f"[DEBUG] Content created")

            # 生成唯一的 message ID
            message_id = str(uuid.uuid4())

            # 發送 start event
            yield f'data: {json.dumps({"type":"start","messageId":message_id})}\n\n'

            # 發送 text-start event
            yield f'data: {json.dumps({"type":"text-start","id":message_id})}\n\n'

            print(f"[DEBUG] Running agent with user_id={user_id}, session_id={session_id}")

            full_response = ""
            event_count = 0
            current_agent = None
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                event_count += 1

                # 追蹤 agent 切換
                event_agent = getattr(event, 'agent_name', None) or getattr(event, 'agent', None)
                if event_agent and event_agent != current_agent:
                    current_agent = event_agent
                    agent_name = current_agent.name if hasattr(current_agent, 'name') else str(current_agent)
                    print(f"[DEBUG] 🔄 Agent switched to: {agent_name}")

                # 顯示 event 類型和 agent
                agent_info = f" (agent: {current_agent.name if hasattr(current_agent, 'name') else current_agent})" if current_agent else ""
                print(f"[DEBUG] Event #{event_count}: {type(event).__name__}{agent_info}")

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_response += part.text
                            print(f"[DEBUG] Yielding text: {part.text[:50]}...")
                            # SSE data stream protocol 格式
                            yield f'data: {json.dumps({"type":"text-delta","id":message_id,"delta":part.text})}\n\n'

            print(f"[DEBUG] Total events: {event_count}, Full response length: {len(full_response)}")

            # 發送 text-end event
            yield f'data: {json.dumps({"type":"text-end","id":message_id})}\n\n'

            # 發送 finish event
            yield f'data: {json.dumps({"type":"finish","finishReason":"stop"})}\n\n'

        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            import traceback
            traceback.print_exc()
            yield f'data: {json.dumps({"type":"error","error":str(e)})}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/stream-test")
async def stream_test():
    """測試 streaming 是否正常"""
    import asyncio

    async def simple_stream():
        for i in range(5):
            yield f"data: message {i}\n\n"
            print(f"[DEBUG] Sent message {i}")
            await asyncio.sleep(0.5)  # 每 0.5 秒發送一次

    return StreamingResponse(
        simple_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/debug")
async def chat_debug(request: Request):
    """Debug endpoint to see raw request"""
    body = await request.json()
    print(f"[DEBUG RAW] {json.dumps(body, indent=2)}")
    return {"received": body}
