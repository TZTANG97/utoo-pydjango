import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.views import APIView

# 并行期说明（Python mall 专用，Java 旧 console 不走本模块）：
# - sy_menu / sy_action / sy_role_* 仍由 Java 与 identity 共用只读；此处不改库、不改登录出参。
# - require_legacy_permission 仅在 Python views 调用；Java Shiro 仍按原 powers 与 JSP 按钮逻辑运行。
# - _LEGACY_MODULE_DOMAINS 只是把 JWT 里已有的 legacy URL 字符串分组，不是调用 Java 模块。


def _decode_identity_jwt(token: str) -> dict:
    """对齐 identity：青岛 token 用 MALL_JWT_SECRET/MALL_JWT_ISSUER，可双密钥试解。"""
    secrets: list[str] = []
    for key in (getattr(settings, "JWT_SECRET", ""), getattr(settings, "MALL_JWT_SECRET", "")):
        if key and key not in secrets:
            secrets.append(key)
    issuers: list[str] = []
    for iss in (getattr(settings, "JWT_ISSUER", ""), getattr(settings, "MALL_JWT_ISSUER", "")):
        if iss and iss not in issuers:
            issuers.append(iss)
    if not secrets:
        raise AuthenticationFailed("JWT 未配置")
    options = {"require": ["exp", "iat", "sub"]}
    decode_attempts: list[tuple[str, str | None]] = []
    for secret in secrets:
        if issuers:
            decode_attempts.extend((secret, iss) for iss in issuers)
        else:
            decode_attempts.append((secret, None))
    for secret, issuer in decode_attempts:
        try:
            kwargs = {"jwt": token, "key": secret, "algorithms": ["HS256"], "options": options}
            if issuer:
                kwargs["issuer"] = issuer
            return jwt.decode(**kwargs)
        except jwt.PyJWTError:
            continue
    raise AuthenticationFailed("JWT 无效或已过期")


def _normalize_legacy_url(url: str) -> str:
    text = (url or "").strip()
    if "?" in text:
        text = text.split("?", 1)[0]
    return text.lstrip("/")


def _legacy_url_stem_variants(url: str) -> set[str]:
    norm = _normalize_legacy_url(url)
    if not norm:
        return set()
    variants = {norm}
    if norm.endswith(".ajax"):
        variants.add(f"{norm[:-5]}.htm")
    elif norm.endswith(".htm"):
        variants.add(f"{norm[:-4]}.ajax")
    return variants


def _legacy_module_prefix(url: str) -> str:
    norm = _normalize_legacy_url(url)
    if not norm:
        return ""
    return norm.split("/", 1)[0]


# 旧版 URL 路径前缀分组（与 Java 版共用 sy_menu/sy_action 里的路径名；仅 Python 校验时使用）。
_LEGACY_MODULE_DOMAINS: tuple[frozenset[str], ...] = (
    frozenset(
        {
            "rentOrder",
            "rentOrderChildForm",
            "loanRentOrder",
            "loanRentOrderChildForm",
            "bill",
            "eveluateCompany",
            "outTreasury",
            "caliOrder",
        }
    ),
    frozenset(
        {
            "saleOrder",
            "saleOrderChildForm",
            "bill",
            "eveluateCompany",
            "outTreasury",
            "funds",
            "paymentapply",
        }
    ),
    frozenset({"purchaseOrder", "bill", "outTreasury", "inTreasury"}),
    frozenset({"productOrder"}),
    frozenset({"inventory", "inventoryCheck", "outTreasury", "inTreasury", "outInventory"}),
    frozenset({"outSaleOrder", "outTreasury"}),
    frozenset({"funds", "bill", "paymentapply"}),
    frozenset({"sys"}),
)


def _expanded_legacy_modules(required_modules: set[str]) -> set[str]:
    expanded = set(required_modules)
    for domain in _LEGACY_MODULE_DOMAINS:
        if domain & required_modules:
            expanded |= domain
    return expanded


def _is_page_permission(perm: str) -> bool:
    return not perm.endswith(".ajax")


def _legacy_permission_set(claims) -> set[str]:
    return {_normalize_legacy_url(url) for url in claims.get("permissions", []) if url}


class JwtRequiredView(APIView):
    """Validate the JWT issued by the identity service and expose its claims."""

    authentication_classes = []

    def perform_authentication(self, request):
        # 各微服务未装 django.contrib.auth；跳过 DRF 默认 AnonymousUser 导入。
        return

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthenticationFailed("缺少 Bearer JWT")
        self.claims = _decode_identity_jwt(token)


def require_write_enabled(setting_name, disabled_message):
    if not getattr(settings, setting_name):
        raise PermissionDenied(disabled_message)


def require_legacy_permission(claims, *legacy_urls):
    """Python mall 专用 legacy 权限（并行期不影响 Java console）。

    JWT permissions 仍来自 identity 只读 sy_menu/sy_action，与 Java selectRolesPowers 同源。
    域内放宽仅当 LEGACY_PERMISSION_DOMAIN_RELAX=true（默认开，仅 Python 进程读取）。
    """
    if claims["scope"]["filter_list"] == 2:
        return
    if not legacy_urls:
        raise PermissionDenied("当前用户没有该操作权限")

    permissions = _legacy_permission_set(claims)
    if not permissions:
        raise PermissionDenied("当前用户没有该操作权限")

    for url in legacy_urls:
        if _legacy_url_stem_variants(url) & permissions:
            return

    if getattr(settings, "LEGACY_PERMISSION_DOMAIN_RELAX", True):
        required_modules = {_legacy_module_prefix(url) for url in legacy_urls if _legacy_module_prefix(url)}
        allowed_modules = _expanded_legacy_modules(required_modules)
        for perm in permissions:
            if _is_page_permission(perm) and _legacy_module_prefix(perm) in allowed_modules:
                return

    raise PermissionDenied("当前用户没有该操作权限")


def get_data_scope(claims):
    scope = claims.get("scope")
    if not isinstance(scope, dict) or "filter_list" not in scope:
        raise PermissionDenied("JWT 缺少数据范围声明")
    return scope

