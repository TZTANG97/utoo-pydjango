from django.urls import path

from apps.orders import views_eveluate

urlpatterns = [
    path("saveEveluate.ajax", views_eveluate.save_eveluate, name="eveluate-save"),
    path("saveEveluateNew.ajax", views_eveluate.save_eveluate_new, name="eveluate-save-new"),
]
