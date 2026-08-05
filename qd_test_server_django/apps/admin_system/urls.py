from django.urls import path

from apps.admin_system.views import app_user as app_user_views
from apps.admin_system.views import area as area_views
from apps.admin_system.views import company_account as company_account_views
from apps.admin_system.views import dept as dept_views
from apps.admin_system.views import district as district_views
from apps.admin_system.views import menu as menu_views
from apps.admin_system.views import role as role_views
from apps.admin_system.views import supplier as supplier_views
from apps.admin_system.views import test_address as test_address_views
from apps.admin_system.views import user as user_views
from apps.admin_system.views import user_company as user_company_views
from apps.admin_system.views import user_type as user_type_views

urlpatterns = [
    # sys/dept
    path("sys/dept/loadAll.ajax", dept_views.dept_tree),
    path("sys/dept/getById.ajax", dept_views.dept_get),
    path("sys/dept/add.ajax", dept_views.dept_add),
    path("sys/dept/update.ajax", dept_views.dept_update),
    path("sys/dept/del.ajax", dept_views.dept_delete),
    path("sys/dept/options.ajax", dept_views.dept_options),
    # sys/user
    path("sys/user/queryUsers.ajax", user_views.user_list),
    path("sys/user/queryUsersExcept.ajax", user_views.user_list_except),
    path("sys/user/queryTestUsers.ajax", user_views.user_query_test_users),
    path("sys/user/queryTestUsers1.ajax", user_views.user_query_test_users1),
    path("sys/user/getById.ajax", user_views.user_get),
    path("sys/user/add.ajax", user_views.user_add),
    path("sys/user/update.ajax", user_views.user_update),
    path("sys/user/del.ajax", user_views.user_disable),
    path("sys/user/updateStatus.ajax", user_views.user_disable),
    path("sys/user/updatePw.ajax", user_views.user_update_password),
    path("sys/user/updateRole.ajax", user_views.user_update_roles),
    path("sys/user/showPowers.ajax", user_views.user_show_powers),
    path("sys/user/logs.ajax", user_views.user_logs),
    path("sys/user/formOptions.ajax", user_views.user_form_options),
    path("sys/user/roleOptions.ajax", user_views.user_role_options),
    path("sys/user/updateAccessRightsQuery.ajax", user_views.user_access_rights_query),
    path("sys/user/updateAccessRights.ajax", user_views.user_access_rights_update),
    path("sys/user/queryUsersAccess.ajax", user_views.user_access_sale_options),
    path("sys/user/queryUsersExpManage.ajax", user_views.user_exp_manage_available),
    path("sys/user/queryExpManageByUser.ajax", user_views.user_exp_manage_list),
    path("sys/user/addUserExpManage.ajax", user_views.user_exp_manage_add),
    path("sys/user/delUserExpManage.ajax", user_views.user_exp_manage_delete),
    # sys/role
    path("sys/role/query.ajax", role_views.role_list),
    path("sys/role/getById.ajax", role_views.role_get),
    path("sys/role/add.ajax", role_views.role_add),
    path("sys/role/update.ajax", role_views.role_update),
    path("sys/role/del.ajax", role_views.role_delete),
    path("sys/role/power/query.ajax", role_views.role_power_get),
    path("sys/role/power/update.ajax", role_views.role_power_save),
    path("sys/role/roleUsers/query.ajax", role_views.role_users_list),
    path("sys/role/roleAddUsers.ajax", role_views.role_add_users),
    path("sys/role/delRoleUsers.ajax", role_views.role_remove_users),
    # sys/menu
    path("sys/menu/query.ajax", menu_views.menu_tree),
    path("sys/menu/getById.ajax", menu_views.menu_get),
    path("sys/menu/add.ajax", menu_views.menu_add),
    path("sys/menu/update.ajax", menu_views.menu_update),
    path("sys/menu/del.ajax", menu_views.menu_delete),
    # sys/district
    path("sys/district/query.ajax", district_views.district_list),
    path("sys/district/children.ajax", district_views.district_children),
    path("sys/district/add.ajax", district_views.district_add),
    path("sys/district/update.ajax", district_views.district_update),
    path("sys/district/del.ajax", district_views.district_delete),
    # sys/userType
    path("sys/userType/query.ajax", user_type_views.user_type_list),
    path("sys/userType/getById.ajax", user_type_views.user_type_get),
    path("sys/userType/add.ajax", user_type_views.user_type_add),
    path("sys/userType/update.ajax", user_type_views.user_type_update),
    path("sys/userType/del.ajax", user_type_views.user_type_delete),
    path("sys/userType/typeRoleOptions.ajax", user_type_views.type_role_options),
    # district (area)
    path("district/getAreaList.ajax", area_views.area_list),
path("district/submitArea.ajax", area_views.area_add),
    path("district/updateArea.ajax", area_views.area_update),
    path("district/updateStatus.ajax", area_views.area_delete),
    path("district/areaOptions.ajax", area_views.area_options),
    # userCompany
    path("userCompany/getUserCompanyList.ajax", user_company_views.company_list),
    path("userCompany/getById.ajax", user_company_views.company_get),
    path("userCompany/getCompanyByComId.ajax", user_company_views.company_get_by_com_id),
    path("userCompany/saveUserCompany.ajax", user_company_views.company_save),
    path("userCompany/updateUserCompany.ajax", user_company_views.company_update),
    path("userCompany/deleteById.ajax", user_company_views.company_delete),
    path("userCompany/updateStatus.ajax", user_company_views.company_update_status),
    path("userCompany/validName.ajax", user_company_views.company_valid_name),
    # supplier (所属公司)
    path("supplier/getSupplierList.ajax", supplier_views.supplier_list),
    path("supplier/getById.ajax", supplier_views.supplier_get),
    path("supplier/saveSupplier.ajax", supplier_views.supplier_save),
    path("supplier/deleteById.ajax", supplier_views.supplier_delete),
    path("supplier/queryAll.ajax", supplier_views.supplier_query_all),
    # appUser
    path("appUser/list.ajax", app_user_views.app_user_list),
    path("appUser/getById.ajax", app_user_views.app_user_detail),
    # testaddress
    path("testaddress/selectalladdress.ajax", test_address_views.address_list),
    path("testaddress/addressList.ajax", test_address_views.address_list_mp),
    path("testaddress/getAddressById.ajax", test_address_views.address_get),
    path("testaddress/addresscreate.ajax", test_address_views.address_create),
    path("testaddress/updateStatus1.ajax", test_address_views.address_update),
    path("testaddress/updateStatus.ajax", test_address_views.address_delete),
    # companyaccount
    path("companyaccount/selectallaccount.ajax", company_account_views.account_list),
    path("companyaccount/accountList.ajax", company_account_views.account_list_mp),
    path("companyaccount/getAddressById.ajax", company_account_views.account_get),
    path("companyaccount/accountcreate.ajax", company_account_views.account_create),
    path("companyaccount/updateStatus1.ajax", company_account_views.account_update),
    path("companyaccount/updateStatus.ajax", company_account_views.account_delete),
    path("companyaccount/defaultaddress.ajax", company_account_views.account_default_get),
    path("companyaccount/updatedefault.ajax", company_account_views.account_default_set),
]
