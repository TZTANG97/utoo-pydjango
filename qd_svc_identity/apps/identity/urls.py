from django.urls import path

from apps.identity import views

urlpatterns = [
    path("auth/login", views.auth_login),
    path("auth/login/", views.auth_login),
    path("auth/refresh", views.auth_refresh),
    path("auth/refresh/", views.auth_refresh),
    path("auth/me", views.auth_me),
    path("auth/me/", views.auth_me),
    path("menus", views.menus),
    path("menus/", views.menus),
    path("permissions", views.permissions),
    path("permissions/", views.permissions),
]
