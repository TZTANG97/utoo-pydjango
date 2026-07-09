from django.urls import path

from apps.orders import views_sample

urlpatterns = [
    path("getAttributeStateList.ajax", views_sample.attribute_state_list),
    path("getStabilityList.ajax", views_sample.stability_list),
]
