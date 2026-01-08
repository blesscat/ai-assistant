from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from ...db.session import get_db
from ...db.models import User
from ...services.token_service import TokenService
from ...config import settings
from ...constants import GOOGLE_CALENDAR_SCOPES


router = APIRouter(prefix="/auth/google", tags=["oauth"])


@router.get("/calendar")
async def initiate_calendar_oauth(user_id: str, db: Session = Depends(get_db)):
    """產生 Google OAuth URL，導向用戶授權 Calendar"""

    # 建立 OAuth URL
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.frontend_url}/api/auth/callback/google-calendar",
        "response_type": "code",
        "scope": " ".join(GOOGLE_CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,  # 用來識別用戶
    }

    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"url": oauth_url}


@router.get("/callback")
async def handle_oauth_callback(
    code: str, state: str, db: Session = Depends(get_db)
):
    """處理 OAuth callback，換取 tokens 並儲存"""

    user_id = state

    try:
        # 換取 tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{settings.frontend_url}/api/auth/callback/google-calendar",
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to exchange code for tokens"
                )

            tokens = response.json()

        # 儲存 tokens
        token_service = TokenService(db)
        await token_service.save_tokens(
            user_id=user_id,
            provider="google_calendar",
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in"),
            scopes=GOOGLE_CALENDAR_SCOPES,
        )

        # 重導回前端
        return RedirectResponse(url=f"{settings.frontend_url}?calendar_connected=true")

    except Exception as e:
        return RedirectResponse(
            url=f"{settings.frontend_url}?calendar_error={str(e)}"
        )


@router.get("/status")
async def check_calendar_status(user_id: str, db: Session = Depends(get_db)):
    """檢查用戶是否已授權 Calendar"""

    token_service = TokenService(db)
    has_token = token_service.has_valid_token(user_id, "google_calendar")

    return {"connected": has_token}


@router.delete("/revoke")
async def revoke_calendar_access(user_id: str, db: Session = Depends(get_db)):
    """撤銷 Calendar 授權"""

    token_service = TokenService(db)
    await token_service.revoke_token(user_id, "google_calendar")

    return {"success": True}
