from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from sqlalchemy.orm import Session

from ..constants import CALENDAR_AGENT_NAME, SUB_AGENT_MODEL, PROMPTS_DIR
from ..tools.calendar_tools import (
    list_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
)
from ..tools.datetime_tools import (
    get_current_time,
    calculate_relative_time,
    get_time_range,
)
from ..db.session import get_db
from ..services.token_service import TokenService
from ..config import settings


def load_instruction(filename: str) -> str:
    """載入 prompt 檔案"""
    path = Path(__file__).parent.parent / PROMPTS_DIR.replace("src/", "") / filename
    return path.read_text(encoding="utf-8")


async def before_calendar_tool(
    tool: BaseTool, args: dict, tool_context: ToolContext
) -> dict | None:
    """在呼叫 calendar tool 前自動注入 access_token"""
    # 只對需要 access_token 的工具注入（calendar 相關工具）
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)

    # 時間工具不需要 access_token
    if any(keyword in tool_name for keyword in ['time', 'datetime', 'get_current', 'calculate', 'get_time_range']):
        return args

    # 從 context 取得 user_id
    user_id = tool_context.user_id

    # 從資料庫取得 access_token
    db = next(get_db())
    try:
        token_service = TokenService(db)
        access_token = await token_service.get_valid_token(
            user_id=user_id,
            provider="google_calendar"
        )

        # 將 access_token 注入到 args 中
        args["access_token"] = access_token
        print(f"[DEBUG] Injected access_token for user {user_id}")

        return args
    except Exception as e:
        print(f"[DEBUG] Failed to get access_token: {e}")
        # 提供預設的空 token，讓 tool 可以執行但會失敗
        args["access_token"] = ""
        return args
    finally:
        db.close()


async def on_calendar_tool_error(
    tool: BaseTool, args: dict, tool_context: ToolContext, error: Exception
) -> dict:
    """處理 calendar tool 錯誤"""
    user_id = tool_context.user_id

    # 檢查是否為授權問題
    error_str = str(error)
    if "credentials" in error_str.lower() or "unauthorized" in error_str.lower() or not args.get("access_token"):
        return {
            "success": False,
            "error": "您尚未授權 Google Calendar 存取權限",
            "need_auth": True,
            "user_id": user_id,
            "auth_url": f"{settings.backend_url}/auth/google/calendar?user_id={user_id}"
        }

    # 其他錯誤
    return {
        "success": False,
        "error": f"執行失敗: {error_str}"
    }


# 建立 Calendar Agent
calendar_agent = LlmAgent(
    name=CALENDAR_AGENT_NAME,
    model=SUB_AGENT_MODEL,
    description="行事曆管理 Agent，處理 Google Calendar 操作",
    instruction=load_instruction("calendar_agent.md"),
    tools=[
        # 時間工具
        FunctionTool(get_current_time),
        FunctionTool(calculate_relative_time),
        FunctionTool(get_time_range),
        # Calendar 工具
        FunctionTool(list_calendar_events),
        FunctionTool(create_calendar_event),
        FunctionTool(update_calendar_event),
        FunctionTool(delete_calendar_event),
    ],
    before_tool_callback=before_calendar_tool,
    on_tool_error_callback=on_calendar_tool_error,
)
