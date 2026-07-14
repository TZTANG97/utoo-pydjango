from django.urls import path

from apps.admin_auth import views

urlpatterns = [
    path("userLogin.ajax", views.user_login, name="admin-legacy-user-login"),
    path("getEncryption.ajax", views.get_encryption, name="admin-legacy-get-encryption"),
]
