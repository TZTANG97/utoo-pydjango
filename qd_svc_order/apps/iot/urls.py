from django.urls import path

from apps.iot import views

urlpatterns = [
    path("device/bind", views.device_bind),
    path("device/bind/", views.device_bind),
    path("device/unbind", views.device_unbind),
    path("device/unbind/", views.device_unbind),
    path("device/binding", views.device_binding),
    path("device/binding/", views.device_binding),
    path("device/resync", views.device_resync),
    path("device/resync/", views.device_resync),
    path("callback/experiment-event", views.callback_experiment_event),
    path("callback/experiment-event/", views.callback_experiment_event),
    path("experiment-data", views.experiment_data),
    path("experiment-data/", views.experiment_data),
]
