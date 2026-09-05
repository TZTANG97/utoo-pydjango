from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from apps.utoo_admin.services.admin_proxy import forward_admin_request


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_admin(request, subpath: str = "", **_kwargs):
    return forward_admin_request(request, request.path)
