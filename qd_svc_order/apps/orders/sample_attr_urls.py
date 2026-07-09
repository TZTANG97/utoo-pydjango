from django.urls import path

from apps.orders import views_sample

urlpatterns = [
    path("sampleattributemanageList.ajax", views_sample.sample_attribute_manage_list),
]
