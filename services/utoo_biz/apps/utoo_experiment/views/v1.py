from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.utoo_experiment.services import admin_order as admin_order_service


class UtooExperimentProxyView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, resource: str):
        return admin_order_service.forward_named_resource(request, resource)

    def post(self, request, resource: str):
        return admin_order_service.forward_named_resource(request, resource)

    def put(self, request, resource: str):
        return admin_order_service.forward_named_resource(request, resource)

    def patch(self, request, resource: str):
        return admin_order_service.forward_named_resource(request, resource)

    def delete(self, request, resource: str):
        return admin_order_service.forward_named_resource(request, resource)
