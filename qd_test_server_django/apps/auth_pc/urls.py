from django.urls import path

from apps.auth_pc import views

urlpatterns = [
    path("login", views.login, name="auth-login"),
    path("refresh", views.refresh, name="auth-refresh"),
    path("me", views.me, name="auth-me"),
]
