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
