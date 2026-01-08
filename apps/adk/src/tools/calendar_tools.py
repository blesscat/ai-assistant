from datetime import datetime
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_calendar_service(access_token: str):
    """建立 Google Calendar 服務"""
    credentials = Credentials(token=access_token)
    return build("calendar", "v3", credentials=credentials)


def list_calendar_events(
    access_token: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    查詢行事曆事件

    Args:
        access_token: Google OAuth access token
        time_min: 開始時間 (ISO 8601 格式)
        time_max: 結束時間 (ISO 8601 格式)
        max_results: 最大回傳數量

    Returns:
        事件列表
    """
    try:
        service = get_calendar_service(access_token)

        if not time_min:
            time_min = datetime.utcnow().isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        return {
            "success": True,
            "events": [
                {
                    "id": event["id"],
                    "summary": event.get("summary", "無標題"),
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                    "description": event.get("description", ""),
                    "location": event.get("location", ""),
                }
                for event in events
            ],
        }
    except HttpError as error:
        return {"success": False, "error": str(error)}


def create_calendar_event(
    access_token: str,
    summary: str,
    start: str,
    end: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: str = "Asia/Taipei",
) -> Dict[str, Any]:
    """
    新增行事曆事件

    Args:
        access_token: Google OAuth access token
        summary: 事件標題
        start: 開始時間 (ISO 8601 格式)
        end: 結束時間 (ISO 8601 格式)
        description: 事件描述
        location: 地點
        timezone: 時區

    Returns:
        新增的事件資訊
    """
    try:
        service = get_calendar_service(access_token)

        event = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }

        if description:
            event["description"] = description
        if location:
            event["location"] = location

        created_event = (
            service.events().insert(calendarId="primary", body=event).execute()
        )

        return {
            "success": True,
            "event": {
                "id": created_event["id"],
                "summary": created_event.get("summary"),
                "start": created_event["start"].get("dateTime"),
                "end": created_event["end"].get("dateTime"),
                "htmlLink": created_event.get("htmlLink"),
            },
        }
    except HttpError as error:
        return {"success": False, "error": str(error)}


def update_calendar_event(
    access_token: str,
    event_id: str,
    summary: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: str = "Asia/Taipei",
) -> Dict[str, Any]:
    """
    修改行事曆事件

    Args:
        access_token: Google OAuth access token
        event_id: 事件 ID
        summary: 事件標題
        start: 開始時間 (ISO 8601 格式)
        end: 結束時間 (ISO 8601 格式)
        description: 事件描述
        location: 地點
        timezone: 時區

    Returns:
        更新後的事件資訊
    """
    try:
        service = get_calendar_service(access_token)

        # 先取得現有事件
        existing_event = (
            service.events().get(calendarId="primary", eventId=event_id).execute()
        )

        # 更新欄位
        if summary is not None:
            existing_event["summary"] = summary
        if start is not None:
            existing_event["start"] = {"dateTime": start, "timeZone": timezone}
        if end is not None:
            existing_event["end"] = {"dateTime": end, "timeZone": timezone}
        if description is not None:
            existing_event["description"] = description
        if location is not None:
            existing_event["location"] = location

        updated_event = (
            service.events()
            .update(calendarId="primary", eventId=event_id, body=existing_event)
            .execute()
        )

        return {
            "success": True,
            "event": {
                "id": updated_event["id"],
                "summary": updated_event.get("summary"),
                "start": updated_event["start"].get("dateTime"),
                "end": updated_event["end"].get("dateTime"),
            },
        }
    except HttpError as error:
        return {"success": False, "error": str(error)}


def delete_calendar_event(access_token: str, event_id: str) -> Dict[str, Any]:
    """
    刪除行事曆事件

    Args:
        access_token: Google OAuth access token
        event_id: 事件 ID

    Returns:
        刪除結果
    """
    try:
        service = get_calendar_service(access_token)
        service.events().delete(calendarId="primary", eventId=event_id).execute()

        return {"success": True, "message": f"事件 {event_id} 已成功刪除"}
    except HttpError as error:
        return {"success": False, "error": str(error)}
