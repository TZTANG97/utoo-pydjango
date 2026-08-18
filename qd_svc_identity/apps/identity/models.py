from django.db import models


class ExpUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    userName = models.CharField(max_length=255, db_column="userName", blank=True, null=True)
    trueName = models.CharField(max_length=255, db_column="trueName", blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    idcard = models.CharField(max_length=255, blank=True, null=True)
    userType = models.IntegerField(db_column="userType", default=1, blank=True, null=True)
    is_identify = models.IntegerField(default=0, blank=True, null=True)
    deleteStatus = models.SmallIntegerField(default=0, blank=True, null=True)
    photo_id = models.BigIntegerField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    area_id = models.CharField(max_length=255, blank=True, null=True)
    address_info = models.CharField(max_length=255, blank=True, null=True)
    wx_nickname = models.CharField(max_length=255, blank=True, null=True)
    identity = models.IntegerField(blank=True, null=True)
    is_accept_message = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "exp_user"


class SystemUser(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    user_name = models.CharField(max_length=64)
    user_password = models.CharField(max_length=64)
    true_name = models.CharField(max_length=64, null=True)
    user_status = models.SmallIntegerField(null=True)
    dept_id = models.CharField(max_length=64, null=True)
    mobile_phone_number = models.CharField(max_length=32, null=True)
    email = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=32, null=True)
    pt_type = models.CharField(max_length=32, null=True)
    last_login_time = models.DateTimeField(null=True)
    last_login_ip = models.CharField(max_length=128, null=True)
    error_count = models.SmallIntegerField(null=True)
    error_time = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = "sy_users"


class Role(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    role_name = models.CharField(max_length=64)
    role_desc = models.CharField(max_length=255, null=True)
    type = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = "sy_role"


class Department(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    dept_sort = models.SmallIntegerField(null=True)
    dept_name = models.CharField(max_length=255)
    dept_phone = models.CharField(max_length=64, null=True)
    dept_fax = models.CharField(max_length=64, null=True)
    dept_address = models.CharField(max_length=255, null=True)
    super_id = models.CharField(max_length=64, null=True)
    lead_uid = models.CharField(max_length=64, null=True)
    dept_desc = models.CharField(max_length=1024, null=True)

    class Meta:
        managed = False
        db_table = "sy_dept"


class Menu(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    menu_super_id = models.CharField(max_length=64, null=True)
    menu_status = models.SmallIntegerField(null=True)
    menu_sort = models.SmallIntegerField(null=True)
    menu_name = models.CharField(max_length=255)
    menu_icon = models.CharField(max_length=255, null=True)
    menu_url = models.CharField(max_length=1024, null=True)
    menu_target = models.CharField(max_length=64, null=True)
    menu_rel = models.CharField(max_length=255, null=True)
    menu_open = models.CharField(max_length=16, null=True)
    menu_external = models.CharField(max_length=16, null=True)
    menu_fresh = models.CharField(max_length=16, null=True)
    pt_type = models.CharField(max_length=50, null=True)

    class Meta:
        managed = False
        db_table = "sy_menu"


class Action(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    menu_id = models.CharField(max_length=64)
    action_name = models.CharField(max_length=255)
    action_url = models.CharField(max_length=2048, null=True)

    class Meta:
        managed = False
        db_table = "sy_action"


class UserRole(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    user_id = models.CharField(max_length=64)
    role_id = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = "sy_user_role"


class RoleMenu(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    role_id = models.CharField(max_length=64)
    menu_id = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = "sy_role_menu"


class RoleAction(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    role_id = models.CharField(max_length=64)
    action_id = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = "sy_role_action"


class UserSalesLink(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=64)
    saleuser_id = models.CharField(max_length=64)
    pt_type = models.CharField(max_length=32, null=True)
    delete_status = models.BooleanField(db_column="deleteStatus", null=True)

    class Meta:
        managed = False
        db_table = "sy_user_saleuser"


class UserCompanyLink(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=64)
    company_id = models.BigIntegerField()
    pt_type = models.CharField(max_length=32, null=True)
    delete_status = models.BooleanField(db_column="deleteStatus", null=True)

    class Meta:
        managed = False
        db_table = "sy_user_company"


class UserOrderTypeLink(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=64)
    type_id = models.BigIntegerField()
    pt_type = models.CharField(max_length=32, null=True)
    delete_status = models.BooleanField(db_column="deleteStatus", null=True)

    class Meta:
        managed = False
        db_table = "sy_user_ordertype"
