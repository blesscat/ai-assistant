from datetime import datetime, timedelta
from typing import Optional
import uuid
import httpx
from sqlalchemy.orm import Session

from ..db.models import UserToken
from ..config import settings


class TokenService:
    def __init__(self, db: Session):
        self.db = db

    async def get_valid_token(
        self, user_id: str, provider: str = "google_calendar"
    ) -> Optional[str]:
        """取得有效的 access_token，過期自動刷新"""
        user_uuid = uuid.UUID(user_id)
        token = (
            self.db.query(UserToken)
            .filter(
                UserToken.user_id == user_uuid,
                UserToken.provider == provider,
            )
            .first()
        )

        if not token:
            return None

        # 檢查是否過期
        if token.expires_at and token.expires_at < datetime.utcnow():
            # 嘗試刷新 token
            if token.refresh_token:
                new_token = await self.refresh_token(token)
                if new_token:
                    return new_token
            return None

        return token.access_token

    async def refresh_token(self, user_token: UserToken) -> Optional[str]:
        """使用 refresh_token 換取新的 access_token"""
        if not user_token.refresh_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "refresh_token": user_token.refresh_token,
                        "grant_type": "refresh_token",
                    },
                )

                if response.status_code != 200:
                    return None

                data = response.json()

                # 更新 token
                user_token.access_token = data["access_token"]
                user_token.expires_at = datetime.utcnow() + timedelta(
                    seconds=data.get("expires_in", 3600)
                )

                # 如果有新的 refresh_token，更新它
                if "refresh_token" in data:
                    user_token.refresh_token = data["refresh_token"]

                self.db.commit()

                return user_token.access_token

        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None

    async def save_tokens(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scopes: Optional[list] = None,
    ) -> UserToken:
        """儲存 OAuth tokens"""
        user_uuid = uuid.UUID(user_id)

        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # 檢查是否已存在
        existing = (
            self.db.query(UserToken)
            .filter(
                UserToken.user_id == user_uuid,
                UserToken.provider == provider,
            )
            .first()
        )

        if existing:
            existing.access_token = access_token
            if refresh_token:
                existing.refresh_token = refresh_token
            if expires_at:
                existing.expires_at = expires_at
            if scopes:
                existing.scopes = scopes
            self.db.commit()
            return existing
        else:
            new_token = UserToken(
                user_id=user_uuid,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                scopes=scopes,
            )
            self.db.add(new_token)
            self.db.commit()
            return new_token

    async def revoke_token(self, user_id: str, provider: str = "google_calendar"):
        """撤銷授權"""
        user_uuid = uuid.UUID(user_id)
        token = (
            self.db.query(UserToken)
            .filter(
                UserToken.user_id == user_uuid,
                UserToken.provider == provider,
            )
            .first()
        )

        if token:
            self.db.delete(token)
            self.db.commit()

    def has_valid_token(self, user_id: str, provider: str = "google_calendar") -> bool:
        """檢查用戶是否已授權"""
        user_uuid = uuid.UUID(user_id)
        token = (
            self.db.query(UserToken)
            .filter(
                UserToken.user_id == user_uuid,
                UserToken.provider == provider,
            )
            .first()
        )

        if not token:
            return False

        # 檢查是否有 refresh_token（可用於刷新）
        if token.refresh_token:
            return True

        # 檢查 access_token 是否未過期
        if token.expires_at and token.expires_at > datetime.utcnow():
            return True

        return False
