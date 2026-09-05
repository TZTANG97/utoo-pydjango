from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from apps.utoo_experiment.services import admin_order as admin_order_service


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_legacy_ajax(request, subpath: str = "", **_kwargs):
    return admin_order_service.forward_legacy_ajax(request, request.path)
