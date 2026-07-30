from django.urls import path

from apps.admin_experiment import views_mp_catalog as views

urlpatterns = [
    path("experimentManage/queryAll.ajax", views.manage_query_all),
    path("experimentManage/queryByParentId.ajax", views.manage_query_by_parent),
    path("experimentProject/list.ajax", views.project_list_java),
    path("experimentGoods/list.ajax", views.goods_list_java),
]
