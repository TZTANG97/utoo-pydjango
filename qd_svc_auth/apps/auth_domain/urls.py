from django.urls import path

from apps.auth_domain import views

urlpatterns = [
    path("login", views.login, name="auth-login"),
    path("refresh", views.refresh, name="auth-refresh"),
    path("me", views.me, name="auth-me"),
    path("basic-info", views.basic_info, name="auth-basic-info"),
    path("update-basic-info", views.update_basic_info, name="auth-update-basic-info"),
    path("set-password", views.set_password, name="auth-set-password"),
    path("upload-avatar", views.upload_avatar, name="auth-upload-avatar"),
    path("update-personal-profile", views.update_personal_profile, name="auth-update-personal-profile"),
    path("update-company-profile", views.update_company_profile, name="auth-update-company-profile"),
]
