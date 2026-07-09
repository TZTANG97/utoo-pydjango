DEFAULT_AVATAR_PATH = "goods/531da299-7156-4ad0-95a4-c94e978c924d.jpg"


def oss_public_base(
    *,
    public_base_url: str = "",
    bucket: str = "qgongye",
    endpoint: str = "https://oss-cn-shanghai.aliyuncs.com",
) -> str:
    explicit = (public_base_url or "").strip()
    if explicit:
        return explicit.rstrip("/")
    endpoint = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{bucket.strip()}.{endpoint}"


def build_oss_object_url(
    path: str | None,
    name: str | None,
    *,
    public_base_url: str = "",
    bucket: str = "qgongye",
    endpoint: str = "https://oss-cn-shanghai.aliyuncs.com",
) -> str:
    base = oss_public_base(
        public_base_url=public_base_url, bucket=bucket, endpoint=endpoint
    )
    p = (path or "").strip()
    n = (name or "").strip()
    if p.startswith("http://") or p.startswith("https://"):
        return p if not n or n in p else f"{p.rstrip('/')}/{n.lstrip('/')}"
    if not p and not n:
        return f"{base}/{DEFAULT_AVATAR_PATH}"
    if p and not n:
        return f"{base}/{p.lstrip('/')}"
    return f"{base}/{p.strip('/')}/{n.lstrip('/')}"


def default_avatar_url(**kwargs) -> str:
    return build_oss_object_url(None, None, **kwargs)
