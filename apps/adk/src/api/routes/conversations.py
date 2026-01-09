from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime
import uuid as uuid_module

from ...db.session import get_db
from ...db.models import Conversation, Message, User


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_db(cls, obj):
        # 將 UUID 轉為字串
        return cls(
            id=str(obj.id),
            user_id=str(obj.user_id),
            title=obj.title,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse]


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "新對話"


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """列出使用者的所有對話（user_id 可以是 UUID 或 google_id）"""
    # 先嘗試用 google_id 查找使用者
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        # 如果不是 google_id，嘗試作為 UUID
        try:
            user_uuid = uuid_module.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, AttributeError):
            return []

    if not user:
        return []

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
        .all()
    )

    return [ConversationResponse.from_db(conv) for conv in conversations]


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(conversation_id: str, user_id: str, db: Session = Depends(get_db)):
    """取得特定對話及其訊息（user_id 可以是 UUID 或 google_id）"""
    # 先找到使用者
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        try:
            user_uuid = uuid_module.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, AttributeError):
            raise HTTPException(status_code=404, detail="User not found")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 將 conversation_id 字串轉為 UUID
    try:
        conv_uuid = uuid_module.UUID(conversation_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Invalid conversation ID")

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_uuid, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conv_uuid).order_by(Message.created_at).all()

    return ConversationWithMessages(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest, user_id: str, db: Session = Depends(get_db)
):
    """建立新對話（user_id 可以是 UUID 或 google_id）"""
    # 先嘗試用 google_id 查找使用者
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        # 如果找不到，建立新使用者
        user = User(
            id=uuid_module.uuid4(),
            google_id=user_id,
            email=f"{user_id}@temp.com",
            name="User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    conversation = Conversation(
        id=uuid_module.uuid4(),
        user_id=user.id,
        title=request.title or "新對話",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse.from_db(conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str, db: Session = Depends(get_db)):
    """刪除對話及其所有訊息（user_id 可以是 UUID 或 google_id）"""
    # 先找到使用者
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        try:
            user_uuid = uuid_module.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, AttributeError):
            raise HTTPException(status_code=404, detail="User not found")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 將 conversation_id 字串轉為 UUID
    try:
        conv_uuid = uuid_module.UUID(conversation_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Invalid conversation ID")

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_uuid, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 刪除相關訊息
    db.query(Message).filter(Message.conversation_id == conv_uuid).delete()

    # 刪除對話
    db.delete(conversation)
    db.commit()

    return {"success": True}


@router.patch("/{conversation_id}/title", response_model=ConversationResponse)
async def update_conversation_title(
    conversation_id: str, user_id: str, title: str, db: Session = Depends(get_db)
):
    """更新對話標題（user_id 可以是 UUID 或 google_id）"""
    # 先找到使用者
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        try:
            user_uuid = uuid_module.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, AttributeError):
            raise HTTPException(status_code=404, detail="User not found")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 將 conversation_id 字串轉為 UUID
    try:
        conv_uuid = uuid_module.UUID(conversation_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Invalid conversation ID")

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_uuid, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.title = title
    db.commit()
    db.refresh(conversation)

    return ConversationResponse.from_db(conversation)
