"""全局 Session Service 管理"""
from google.adk.sessions import InMemorySessionService

# 創建全局的 session service 實例
# 這樣可以在多個請求之間保持對話狀態，避免每次傳遞完整歷史
global_session_service = InMemorySessionService()


def get_session_service() -> InMemorySessionService:
    """獲取全局 session service"""
    return global_session_service
