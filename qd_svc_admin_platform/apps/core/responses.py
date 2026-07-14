def api_ok(data=None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def api_fail(code: int, message: str, data=None) -> dict:
    return {"code": code, "message": message, "data": data}


def ajax_ok(obj=None, res_msg: str = "操作成功") -> dict:
    return {"res": True, "resMsg": res_msg, "obj": obj}


def ajax_fail(res_msg: str = "操作失败", obj=None) -> dict:
    return {"res": False, "resMsg": res_msg, "obj": obj}
