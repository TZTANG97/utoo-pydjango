"""
统一 API 响应（对齐 docs/前后端接口迁移.md 与 FastAPI app/schemas/response.py）
"""


def api_ok(data=None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def api_fail(code: int, message: str, data=None) -> dict:
    return {"code": code, "message": message, "data": data}


def ajax_ok(obj=None, res_msg: str = "操作成功") -> dict:
    """Java 兼容：res=1, resMsg, obj"""
    return {"res": 1, "resMsg": res_msg, "obj": obj}


def ajax_fail(res_msg: str = "操作失败", obj=None) -> dict:
    return {"res": 0, "resMsg": res_msg, "obj": obj}
