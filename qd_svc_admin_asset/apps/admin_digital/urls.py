from django.urls import path

from apps.admin_digital.views import digital as views

urlpatterns = [
    # 公共
    path("digital/deptOptions.ajax", views.dept_options),
    # 统计看板
    path("testUserStats/overview.ajax", views.stats_overview),
    path("testUserStats/queryAllDept.ajax", views.dept_options),
    # 实验室人员产出计划
    path("testUserPerformance/queryUsers.ajax", views.test_user_list),
    path("testUserPerformance/selAmountByYear.ajax", views.test_target_get),
    path("testUserPerformance/setPerformance.ajax", views.test_target_save),
    path("testUserPerformance/showByUserId.ajax", views.test_target_show),
    # 销售人员产出计划
    path("saleUserPerformance/queryUsers.ajax", views.sale_user_list),
    path("saleUserPerformance/selAmountByYear.ajax", views.sale_target_get),
    path("saleUserPerformance/setPerformance.ajax", views.sale_target_save),
    path("saleUserPerformance/showByUserId.ajax", views.sale_target_show),
    # 实验室测试人员绩效
    path("labPerformance/selByYear.ajax", views.lab_test_perf),
    # 实验室销售人员绩效
    path("labPerformanceSaleuser/selUsersByDeptId.ajax", views.lab_sale_users),
    path("labPerformanceSaleuser/selByYear.ajax", views.lab_sale_perf),
]
