from django.urls import path

from apps.admin_fund.views import fund as views

urlpatterns = [
    # 资金账户设置 / 美金汇率
    path("funds/accountGet.ajax", views.setting_get),
    path("funds/account_save.ajax", views.setting_save_rates),
    path("funds/saveUSExchangeRate.ajax", views.setting_save_exchange),
    # 资金账户一览
    path("funds/fundAccountList.ajax", views.account_list),
    path("funds/userAccountDetail.ajax", views.account_user_detail),
    path("funds/account_userId.htm", views.account_user_balance),
    path("account_User.ajax", views.account_user_list_mp),
    # 资金账户 / 资金管理
    path("funds/assetAcc.ajax", views.asset_overview),
    path("funds/assetAccxcx.ajax", views.asset_overview),
    path("funds/assetAccountxcx.ajax", views.asset_account_xcx),
    path("yesterdayIncomexcx.ajax", views.yesterday_income_xcx),
    path("yesterdayIncome.ajax", views.yesterday_income_xcx),
    path("getLog.ajax", views.account_log_list),
    path("getAccountLog.ajax", views.account_log_list),
    path("funds/getAccountLog.ajax", views.account_log_list),
    path("selExpSumByYear.ajax", views.exp_sum_by_year),
    path("selExpSumByYearxcx.ajax", views.exp_sum_by_year),
    path("funds/selExpSumByYear.ajax", views.exp_sum_by_year),
    path("funds/selExpSumByYearxcx.ajax", views.exp_sum_by_year),
    path("funds/fundYears.ajax", views.fund_years),
    path("funds/accountLog_add.ajax", views.account_log_add),
    path("funds/account_transfer_add.ajax", views.account_transfer_add),
    path("funds/account_loan_add.ajax", views.account_loan_add),
    path("funds/submit_chargeback.ajax", views.chargeback_add),
    path("funds/account_loan_clear_add.ajax", views.loan_clear_add),
    path("funds/fundUsers.ajax", views.fund_user_options),
    path("pass.ajax", views.account_log_pass),
    path("funds/pass.ajax", views.account_log_pass),
    # 选项
    path("companyPay/queryCompanies.ajax", views.company_options),
    path("supplier/queryAllPay.ajax", views.company_options),
    path("userPay/queryAllUserPay.ajax", views.user_pay_options),
    path("projectPay/queryLabs.ajax", views.lab_options),
    # 各公司资金支出
    path("companyPay/selDetailList.ajax", views.company_pay_list),
    path("companyPay/submitCompanyPay.ajax", views.company_pay_save),
    path("companyPay/chargeBack.ajax", views.company_pay_charge_back),
    path("companyPay/companyPayUpdate.ajax", views.company_pay_update),
    # 个人资金支出
    path("userPay/selDetailList.ajax", views.user_pay_list),
    path("userPay/submitUserPay.ajax", views.user_pay_save),
    path("userPay/chargeBack.ajax", views.user_pay_charge_back),
    path("userPay/companyPayUpdate.ajax", views.user_pay_update),
    # 各公司借贷款还款
    path("companyLoanPay/selDetailList.ajax", views.company_loan_list),
    path("companyLoanPay/submitCompanyPay.ajax", views.company_loan_save),
    # 各项目资金支出
    path("projectPay/selDetailList.ajax", views.project_pay_list),
    path("projectPay/submitUserPay.ajax", views.project_pay_save),
    # 数字化管理运营中心
    path("digitalManage/overview.ajax", views.digital_overview),
    path("digitalManage/selCompanySaleByYear.ajax", views.digital_company_sale_by_year),
    path("digitalManage/selExpSaleByYear.ajax", views.digital_exp_sale_by_year),
    path("digitalManage/selExpReceivePie.ajax", views.digital_exp_receive_pie),
    # 非管理员个人看板（公司基金 CS04 等）
    path("digitalManage/selUserAmountByYearsygr.ajax", views.digital_user_amount_sygr),
    path("digitalManage/selUserAmountByYearsyfbgr.ajax", views.digital_user_amount_syfbgr),
    path("digitalManage/selUserOverduePie.ajax", views.digital_user_overdue_pies),
]
