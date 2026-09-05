from django.urls import path

from apps.wx import views

urlpatterns = [
    path("WeChatQRCodeGenerator.ajax", views.wechat_qr_generator, name="wx-qr"),
    path("qrScanStatusCheck.ajax", views.qr_scan_status_check, name="wx-qr-check"),
    path("wechatconfig.ajax", views.wechatconfig, name="wx-gzh-callback"),
    path("reservationDetail.ajax", views.reservation_detail, name="wx-reservation"),
    path("addFeedBack.ajax", views.add_feedback, name="wx-feedback"),
]
