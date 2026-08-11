from django.urls import path

from apps.iot import views

urlpatterns = [
    path("auth/login", views.auth_login),
    path("auth/login/", views.auth_login),
    path("auth/status", views.auth_status),
    path("auth/status/", views.auth_status),
    path("auth/logout", views.auth_logout),
    path("auth/logout/", views.auth_logout),
    path("device/list", views.device_list),
    path("device/list/", views.device_list),
    path("device/bind", views.device_bind),
    path("device/bind/", views.device_bind),
    path("task/create", views.create_task),
    path("task/create/", views.create_task),
    path("sso/jump", views.sso_jump),
    path("sso/jump/", views.sso_jump),
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
