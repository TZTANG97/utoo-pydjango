from django.urls import path

from apps.invoices import views

urlpatterns = [
    path("invoiceDetail.ajax", views.invoice_detail),
]
