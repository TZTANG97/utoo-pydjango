from django.urls import path

from apps.orders import views_list_dpt

urlpatterns = [
    path("list_dpt.ajax", views_list_dpt.experiment_sub_order_list_dpt, name="experiment-sub-list_dpt"),
]
