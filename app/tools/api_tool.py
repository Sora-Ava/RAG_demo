"""
通用外部 HTTP 工具 —— 支持 GET / POST，可配置请求头与参数
"""
import json as json_lib
from typing import Optional

import httpx
from langchain_core.tools import tool
from loguru import logger

# 默认超时（秒）
_DEFAULT_TIMEOUT = 15


@tool
def http_request(
    url: str,
    method: str = "GET",
    params: Optional[str] = None,
    body: Optional[str] = None,
    headers: Optional[str] = None,
) -> str:
    """
    发起一次 HTTP 请求并返回响应内容。
    适用于需要调用外部 REST API、查询公开数据接口的场景。

    Args:
        url:     请求 URL，必须包含协议头（http:// 或 https://）
        method:  请求方法，"GET" 或 "POST"（默认 GET）
        params:  URL 查询参数，JSON 字符串格式，例如 '{"key": "value"}'
        body:    POST 请求体，JSON 字符串格式，例如 '{"name": "张三"}'
        headers: 自定义请求头，JSON 字符串格式，例如 '{"Authorization": "Bearer token"}'
    """
    logger.info(f"[HTTP] {method} {url}")

    # 解析可选的 JSON 字符串参数
    def _parse_json_str(s: Optional[str], field_name: str) -> dict:
        if not s:
            return {}
        try:
            return json_lib.loads(s)
        except json_lib.JSONDecodeError as e:
            raise ValueError(f"{field_name} 不是合法的 JSON 字符串: {e}") from e

    parsed_params = _parse_json_str(params, "params")
    parsed_body = _parse_json_str(body, "body")
    parsed_headers = _parse_json_str(headers, "headers")

    method = method.upper()
    if method not in ("GET", "POST"):
        return f"不支持的请求方法: {method}，仅支持 GET / POST"

    try:
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as client:
            if method == "GET":
                resp = client.get(url, params=parsed_params, headers=parsed_headers)
            else:
                resp = client.post(
                    url, json=parsed_body, params=parsed_params, headers=parsed_headers
                )

        resp.raise_for_status()

        # 尝试返回 JSON，否则返回文本（截断过长响应）
        try:
            result = resp.json()
            return json_lib.dumps(result, ensure_ascii=False, indent=2)[:3000]
        except Exception:
            return resp.text[:3000]

    except httpx.HTTPStatusError as e:
        return f"HTTP 错误 {e.response.status_code}: {e.response.text[:500]}"
    except httpx.TimeoutException:
        return f"请求超时（>{_DEFAULT_TIMEOUT}s）: {url}"
    except Exception as e:
        return f"请求失败: {e}"
