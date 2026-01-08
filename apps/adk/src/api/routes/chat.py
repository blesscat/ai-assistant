import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ...db.session import get_db
from ...agents.root_agent import root_agent
from ...services.token_service import TokenService


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

            # 每次請求建立新的 session service 和 runner
            local_session_service = InMemorySessionService()

            # 建立 Runner (API key 已在 root_agent.py 中設定為環境變數)
            runner = Runner(
                app_name="agents",
                agent=root_agent,
                session_service=local_session_service,
            )
            print("[DEBUG] Runner created")

            # 取得最後一則訊息
            last_message = request.messages[-1] if request.messages else None
            if not last_message:
                yield 'data: {"type":"error","error":"No message provided"}\n\n'
                return

            # 建立 content
            content = types.Content(
                role="user",
                parts=[types.Part(text=last_message.content)],
            )
            print(f"[DEBUG] Content created: {content}")

            # 執行 agent
            user_id = request.user_id or "anonymous"
            session_id = str(uuid.uuid4())
            print(f"[DEBUG] Creating session with user_id={user_id}, session_id={session_id}")

            # 先建立 session
            session = await local_session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id,
            )
            print(f"[DEBUG] Session created: {session}")

            # 生成唯一的 message ID
            message_id = str(uuid.uuid4())

            # 發送 start event
            yield f'data: {json.dumps({"type":"start","messageId":message_id})}\n\n'

            # 發送 text-start event
            yield f'data: {json.dumps({"type":"text-start","id":message_id})}\n\n'

            print(f"[DEBUG] Running agent with user_id={user_id}, session_id={session_id}")

            full_response = ""
            event_count = 0
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                event_count += 1
                print(f"[DEBUG] Event #{event_count}: {type(event).__name__}")

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
