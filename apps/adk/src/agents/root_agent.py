import os
from pathlib import Path
from google.adk.agents import LlmAgent

from ..constants import ROOT_AGENT_NAME, ROOT_AGENT_MODEL, PROMPTS_DIR
from ..config import settings
from .calendar_agent import calendar_agent


def load_instruction(filename: str) -> str:
    """載入 prompt 檔案"""
    path = Path(__file__).parent.parent / PROMPTS_DIR.replace("src/", "") / filename
    return path.read_text(encoding="utf-8")


# 設定 Google API key 環境變數
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# 建立 Root Agent
root_agent = LlmAgent(
    name=ROOT_AGENT_NAME,
    model=ROOT_AGENT_MODEL,
    description="主要助理，負責協調任務分配",
    instruction=load_instruction("root_agent.md"),
    sub_agents=[calendar_agent],
)
