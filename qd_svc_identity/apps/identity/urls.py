from django.urls import path

from apps.identity import views
from apps.identity import views_org as org

urlpatterns = [
    path("auth/login", views.auth_login),
    path("auth/login/", views.auth_login),
    path("auth/refresh", views.auth_refresh),
    path("auth/refresh/", views.auth_refresh),
    path("auth/me", views.auth_me),
    path("auth/me/", views.auth_me),
    path("auth/password", org.ChangeMyPasswordView.as_view()),
    path("auth/password/", org.ChangeMyPasswordView.as_view()),
    path("auth/data-scope", org.DataScopeView.as_view()),
    path("auth/data-scope/", org.DataScopeView.as_view()),
    path("permissions", views.permissions),
    path("permissions/", views.permissions),
    path("menus/all", org.MenuAdminTreeView.as_view()),
    path("menus/all/", org.MenuAdminTreeView.as_view()),
    path("menus/<str:menu_id>", org.MenuDetailView.as_view()),
    path("menus", views.menus),
    path("menus/", views.menus),
    path("departments/<str:dept_id>", org.DepartmentDetailView.as_view()),
    path("departments", org.DepartmentTreeView.as_view()),
    path("roles/<str:role_id>/menus", org.RoleMenuView.as_view()),
    path("roles/<str:role_id>/actions", org.RoleActionView.as_view()),
    path("roles/<str:role_id>", org.RoleDetailView.as_view()),
    path("roles", org.RoleListView.as_view()),
    path("users/<str:user_id>/roles", org.UserRoleView.as_view()),
    path("users/<str:user_id>/data-scope", org.DataScopeView.as_view()),
    path("users/<str:user_id>/password", org.UserPasswordView.as_view()),
    path("users/<str:user_id>/access", org.UserAccessView.as_view()),
    path("users/<str:user_id>/status", org.UserStatusView.as_view()),
    path("users/<str:user_id>", org.UserDetailView.as_view()),
    path("users", org.UserListView.as_view()),
]
