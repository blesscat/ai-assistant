from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.models import User


router = APIRouter(prefix="/api/users", tags=["users"])


class CreateUserRequest(BaseModel):
    google_id: str
    email: EmailStr
    name: Optional[str] = None
    image: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    google_id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/sync", response_model=UserResponse)
async def sync_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    """
    同步用戶資訊：如果用戶不存在則創建，存在則更新
    用於 NextAuth 登入後同步用戶資訊到資料庫
    """
    # 檢查用戶是否已存在
    user = db.query(User).filter(User.google_id == request.google_id).first()

    if user:
        # 更新現有用戶資訊
        user.email = request.email
        user.name = request.name
        user.image = request.image
        db.commit()
        db.refresh(user)
        print(f"[DEBUG] Updated user: {user.email}")
    else:
        # 創建新用戶
        user = User(
            google_id=request.google_id,
            email=request.email,
            name=request.name,
            image=request.image,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[DEBUG] Created new user: {user.email}")

    return UserResponse(
        id=str(user.id),
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        image=user.image,
    )


@router.get("/{google_id}", response_model=UserResponse)
async def get_user(google_id: str, db: Session = Depends(get_db)):
    """根據 google_id 查詢用戶"""
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        image=user.image,
    )
