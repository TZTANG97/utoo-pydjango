from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from apps.utoo_consumer.services.consumer_proxy import forward_consumer_request


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_consumer(request, subpath: str = "", **_kwargs):
    return forward_consumer_request(request, request.path)
