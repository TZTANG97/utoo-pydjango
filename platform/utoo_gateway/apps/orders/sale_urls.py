from django.urls import path

from apps.orders import views_mp_actions

urlpatterns = [
    path("makeFrontOrder.ajax", views_mp_actions.make_front_order, name="sale-makeFrontOrder"),
]
