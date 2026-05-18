"""统一 API 响应格式工具函数。"""


def success_response(data, code=200):
    """返回成功响应。
    Args:
        data: 响应数据
        code: 业务状态码（非 HTTP 状态码）
    Returns:
        统一格式的响应字典
    """
    return {"success": True, "data": data, "error": None, "code": code}


def error_response(message, code=500):
    """返回错误响应。
    Args:
        message: 错误描述
        code: 业务状态码（非 HTTP 状态码）
    Returns:
        统一格式的响应字典
    """
    return {"success": False, "data": None, "error": message, "code": code}
