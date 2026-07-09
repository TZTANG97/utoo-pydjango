"""兼容旧前端 axios 默认 Accept: '*'（DRF 会返回 406）"""


class NormalizeAcceptHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        accept = (request.META.get("HTTP_ACCEPT") or "").strip()
        if accept in ("*", "''", '""'):
            request.META["HTTP_ACCEPT"] = "*/*"
        return self.get_response(request)
