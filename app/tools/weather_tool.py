"""
天气查询工具 —— 模拟实现（可一键替换真实 API）
替换真实 API：将 _fetch_real_weather() 中的逻辑改为调用
OpenWeatherMap / 和风天气 / 心知天气等接口即可
"""
import random
from langchain_core.tools import tool
from loguru import logger


# ──────────────────────────────────────────────────────────────────────────────
# 模拟天气数据（生产环境替换为真实 API 调用）
# ──────────────────────────────────────────────────────────────────────────────

_MOCK_CONDITIONS = ["晴", "多云", "阴", "小雨", "中雨", "雷阵雨", "雪", "雾"]
_MOCK_WIND_DIRECTIONS = ["东风", "南风", "西风", "北风", "东南风", "西北风"]


def _fetch_weather(city: str) -> dict:
    """
    【模拟实现】返回随机天气数据。
    替换真实 API 时修改此函数，返回相同的字典结构即可。

    真实 API 示例（和风天气）：
        import httpx
        resp = httpx.get(
            "https://devapi.qweather.com/v7/weather/now",
            params={"location": city, "key": "YOUR_KEY"},
            timeout=10,
        )
        data = resp.json()["now"]
        return {
            "city": city,
            "condition": data["text"],
            "temperature": data["temp"],
            "humidity": data["humidity"],
            "wind": data["windDir"] + data["windScale"] + "级",
        }
    """
    temp = random.randint(-5, 40)
    humidity = random.randint(20, 95)
    condition = random.choice(_MOCK_CONDITIONS)
    wind = random.choice(_MOCK_WIND_DIRECTIONS) + f"{random.randint(1, 8)} 级"
    return {
        "city": city,
        "condition": condition,
        "temperature": temp,
        "humidity": humidity,
        "wind": wind,
    }


# ──────────────────────────────────────────────────────────────────────────────
# LangChain 工具定义
# ──────────────────────────────────────────────────────────────────────────────

@tool
def weather_query(city: str) -> str:
    """
    查询指定城市的实时天气信息，包括天气状况、温度、湿度和风力。
    适用于用户询问天气、出行建议等场景。

    Args:
        city: 城市名称，例如 "北京"、"上海"、"广州"
    """
    logger.info(f"[Weather] 查询城市: {city!r}")

    data = _fetch_weather(city)
    return (
        f"📍 {data['city']} 当前天气\n"
        f"  天气状况: {data['condition']}\n"
        f"  温度: {data['temperature']}°C\n"
        f"  湿度: {data['humidity']}%\n"
        f"  风力: {data['wind']}\n"
        f"（数据来源: 模拟天气服务 —— 可替换为真实 API）"
    )
