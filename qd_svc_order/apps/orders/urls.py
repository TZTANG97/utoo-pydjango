from django.urls import path

from apps.orders import views
from apps.orders import views_list_dpt

urlpatterns = [
    path("list_dpt.ajax", views_list_dpt.experiment_order_list_dpt, name="experiment-list_dpt"),
    path("uploadChildData.ajax", views.upload_child_data, name="experiment-uploadChildData"),
    path("loadaccessory.ajax", views.load_accessory, name="experiment-loadaccessory"),
    path("printpdf.ajax", views.print_pdf, name="experiment-printpdf"),
    path("orderdetail.ajax", views.order_detail, name="experiment-orderdetail"),
    path(
        "getChildFormByIdExp.ajax",
        views.get_child_form_by_id_exp,
        name="experiment-getChildFormByIdExp",
    ),
]
