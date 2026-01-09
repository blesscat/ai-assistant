from datetime import datetime, timedelta
from typing import Dict, Any
from zoneinfo import ZoneInfo


def get_current_time(timezone: str = "Asia/Taipei") -> Dict[str, Any]:
    """
    獲取當前時間

    Args:
        timezone: 時區，預設為 Asia/Taipei

    Returns:
        當前時間資訊
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)

        return {
            "success": True,
            "current_time": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime_str": now.strftime("%Y年%m月%d日 %H:%M:%S"),
            "weekday": now.strftime("%A"),
            "weekday_zh": _get_weekday_zh(now.weekday()),
            "timezone": timezone,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def calculate_relative_time(
    relative_description: str,
    timezone: str = "Asia/Taipei"
) -> Dict[str, Any]:
    """
    計算相對時間（例如：今天、明天、下週一、下個月等）

    Args:
        relative_description: 相對時間描述（today, tomorrow, next_monday, next_week, next_month）
        timezone: 時區，預設為 Asia/Taipei

    Returns:
        計算後的時間資訊
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        target_date = None

        # 轉換為小寫並移除空格
        desc = relative_description.lower().strip()

        if desc in ["today", "今天"]:
            target_date = now
        elif desc in ["tomorrow", "明天"]:
            target_date = now + timedelta(days=1)
        elif desc in ["yesterday", "昨天"]:
            target_date = now - timedelta(days=1)
        elif desc in ["next_week", "下週", "下星期"]:
            target_date = now + timedelta(weeks=1)
        elif desc in ["next_month", "下個月"]:
            # 簡單處理：加30天
            target_date = now + timedelta(days=30)
        elif desc.startswith("next_") or desc.startswith("下週"):
            # 處理下週特定日期 (next_monday, 下週一)
            weekday_map = {
                "monday": 0, "週一": 0, "星期一": 0,
                "tuesday": 1, "週二": 1, "星期二": 1,
                "wednesday": 2, "週三": 2, "星期三": 2,
                "thursday": 3, "週四": 3, "星期四": 3,
                "friday": 4, "週五": 4, "星期五": 4,
                "saturday": 5, "週六": 5, "星期六": 5,
                "sunday": 6, "週日": 6, "星期日": 6, "週天": 6,
            }

            for day_name, day_num in weekday_map.items():
                if day_name in desc:
                    days_ahead = day_num - now.weekday()
                    if days_ahead <= 0:  # 如果今天是目標日或已過，則加7天
                        days_ahead += 7
                    target_date = now + timedelta(days=days_ahead)
                    break
        elif "後天" in desc:
            target_date = now + timedelta(days=2)
        elif "前天" in desc:
            target_date = now - timedelta(days=2)
        elif "天後" in desc or "days" in desc:
            # 處理 N 天後
            try:
                import re
                match = re.search(r'(\d+)', desc)
                if match:
                    days = int(match.group(1))
                    target_date = now + timedelta(days=days)
            except:
                pass

        if target_date is None:
            return {
                "success": False,
                "error": f"無法解析相對時間描述: {relative_description}"
            }

        # 設定時間為當天的開始 (00:00:00)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # 設定時間為當天的結束 (23:59:59)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return {
            "success": True,
            "date": target_date.strftime("%Y-%m-%d"),
            "start_time": start_of_day.isoformat(),
            "end_time": end_of_day.isoformat(),
            "datetime_str": target_date.strftime("%Y年%m月%d日"),
            "weekday": target_date.strftime("%A"),
            "weekday_zh": _get_weekday_zh(target_date.weekday()),
            "timezone": timezone,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_time_range(
    start_relative: str,
    end_relative: str = None,
    timezone: str = "Asia/Taipei"
) -> Dict[str, Any]:
    """
    獲取時間範圍（用於查詢行事曆）

    Args:
        start_relative: 開始時間的相對描述
        end_relative: 結束時間的相對描述（選填，預設為開始時間的當天結束）
        timezone: 時區，預設為 Asia/Taipei

    Returns:
        時間範圍資訊
    """
    try:
        start_result = calculate_relative_time(start_relative, timezone)
        if not start_result["success"]:
            return start_result

        if end_relative:
            end_result = calculate_relative_time(end_relative, timezone)
            if not end_result["success"]:
                return end_result
            end_time = end_result["end_time"]
        else:
            # 如果沒有指定結束時間，使用開始日期的結束時間
            end_time = start_result["end_time"]

        return {
            "success": True,
            "start_time": start_result["start_time"],
            "end_time": end_time,
            "start_date_str": start_result["datetime_str"],
            "end_date_str": end_result["datetime_str"] if end_relative else start_result["datetime_str"],
            "timezone": timezone,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _get_weekday_zh(weekday: int) -> str:
    """將 weekday 數字轉換為中文"""
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    return weekday_map.get(weekday, "")
