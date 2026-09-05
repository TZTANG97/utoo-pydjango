from django.urls import path

from apps.utoo_experiment.views.v1 import UtooExperimentProxyView

urlpatterns = [
    path("utoo/<str:resource>", UtooExperimentProxyView.as_view()),
]
