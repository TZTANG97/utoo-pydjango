from django.db.models import Q

from apps.identity.models import SystemUser, UserRole


def get_by_id(user_id):
    return SystemUser.objects.filter(id=user_id).first()


def list_admin(*, keyword="", include_disabled=False, limit=200, pt_type="1"):
    rows = SystemUser.objects.filter(pt_type__contains=pt_type)
    if not include_disabled:
        rows = rows.filter(user_status=1)
    if keyword:
        rows = rows.filter(Q(user_name__icontains=keyword) | Q(true_name__icontains=keyword))
    return list(rows.order_by("user_name")[:limit])


def username_exists(user_name, *, exclude_id=None):
    rows = SystemUser.objects.filter(user_name=user_name)
    if exclude_id:
        rows = rows.exclude(id=exclude_id)
    return rows.exists()


def save_user(user, *, update_fields=None):
    if update_fields is not None:
        user.save(update_fields=update_fields)
    else:
        user.save()
    return user


def list_role_ids(user_id):
    return list(UserRole.objects.filter(user_id=user_id).values_list("role_id", flat=True))


def delete_user_roles(user_id):
    UserRole.objects.filter(user_id=user_id).delete()


def bulk_create_user_roles(rows):
    UserRole.objects.bulk_create(rows)
