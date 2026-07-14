from django.urls import path

from apps.admin_experiment import views

urlpatterns = [
    path("adminExperiment/health.ajax", views.health_probe),
    # 业务类目
    path("adminExperiment/manage/list.ajax", views.manage_list),
    path("adminExperiment/manage/get.ajax", views.manage_get),
    path("adminExperiment/manage/save.ajax", views.manage_save),
    path("adminExperiment/manage/updateStatus.ajax", views.manage_status),
    path("adminExperiment/manage/del.ajax", views.manage_del),
    path("adminExperiment/manage/options.ajax", views.manage_options),
    # 测试项目
    path("adminExperiment/project/list.ajax", views.project_list),
    path("adminExperiment/project/get.ajax", views.project_get),
    path("adminExperiment/project/save.ajax", views.project_save),
    path("adminExperiment/project/del.ajax", views.project_del),
    # 实验产品
    path("adminExperiment/goods/list.ajax", views.goods_list),
    path("adminExperiment/goods/get.ajax", views.goods_get),
    path("adminExperiment/goods/save.ajax", views.goods_save),
    path("adminExperiment/goods/del.ajax", views.goods_del),
    # 实验品牌 type=2
    path("adminExperiment/brand/list.ajax", views.brand_list),
    path("adminExperiment/brand/get.ajax", views.brand_get),
    path("adminExperiment/brand/save.ajax", views.brand_save),
    path("adminExperiment/brand/del.ajax", views.brand_del),
    path("adminExperiment/brand/options.ajax", views.brand_options),
    # 样品属性
    path("adminExperiment/sampleAttr/list.ajax", views.sample_attr_list),
    path("adminExperiment/sampleAttr/get.ajax", views.sample_attr_get),
    path("adminExperiment/sampleAttr/save.ajax", views.sample_attr_save),
    path("adminExperiment/sampleAttr/updateStatus.ajax", views.sample_attr_status),
    path("adminExperiment/sampleAttr/del.ajax", views.sample_attr_del),
    path("adminExperiment/sampleAttr/options.ajax", views.sample_attr_options),
    # 订单 / 抢单
    path("adminExperiment/order/list.ajax", views.order_list),
    path("adminExperiment/order/detail.ajax", views.order_detail),
    path("adminExperiment/order/audit.ajax", views.order_audit),
    path("adminExperiment/order/export.ajax", views.order_export),
    path("adminExperiment/order/statusOptions.ajax", views.order_status_options),
    path("adminExperiment/grab/list.ajax", views.grab_list),
    path("adminExperiment/grab/competition.ajax", views.grab_order),
]
