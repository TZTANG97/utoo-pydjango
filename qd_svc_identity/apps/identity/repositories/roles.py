from apps.identity.models import Action, Menu, Role, RoleAction, RoleMenu, UserRole


def get_platform_by_id(role_id, role_type: int):
    return Role.objects.filter(id=role_id, type=role_type).first()


def list_platform(*, keyword="", limit=500, role_type: int = 1):
    rows = Role.objects.filter(type=role_type)
    if keyword:
        rows = rows.filter(role_name__icontains=keyword)
    return list(rows.order_by("role_name").values("id", "role_name", "role_desc", "type")[:limit])


def role_name_exists(role_name, *, exclude_id=None, role_type: int = 1):
    rows = Role.objects.filter(role_name=role_name, type=role_type)
    if exclude_id:
        rows = rows.exclude(id=exclude_id)
    return rows.exists()


def find_existing_ids(role_ids, role_type: int):
    if not role_ids:
        return set()
    return set(Role.objects.filter(id__in=role_ids, type=role_type).values_list("id", flat=True))


def save_role(role, *, update_fields=None):
    if update_fields is not None:
        role.save(update_fields=update_fields)
    else:
        role.save()
    return role


def delete_role(role):
    role.delete()


def list_menu_ids(role_id, *, pt_type=None):
    rows = RoleMenu.objects.filter(role_id=role_id).exclude(menu_id__in=["", "0"])
    if pt_type:
        platform_menu_ids = Menu.objects.filter(pt_type__contains=pt_type).values("id")
        rows = rows.filter(menu_id__in=platform_menu_ids)
    return list(rows.values_list("menu_id", flat=True))


def list_action_ids(role_id):
    return list(RoleAction.objects.filter(role_id=role_id).values_list("action_id", flat=True))


def role_has_users(role_id):
    return UserRole.objects.filter(role_id=role_id).exists()


def delete_role_menus(role_id):
    RoleMenu.objects.filter(role_id=role_id).delete()


def delete_role_actions(role_id):
    RoleAction.objects.filter(role_id=role_id).delete()


def bulk_create_role_menus(rows):
    RoleMenu.objects.bulk_create(rows)


def bulk_create_role_actions(rows):
    RoleAction.objects.bulk_create(rows)


def find_existing_menu_ids(menu_ids, *, pt_type: str | None = None):
    if not menu_ids:
        return set()
    rows = Menu.objects.filter(id__in=menu_ids).exclude(id__in=["", "0"])
    if pt_type:
        rows = rows.filter(pt_type__contains=pt_type)
    return set(rows.values_list("id", flat=True))


def find_existing_action_ids(action_ids):
    if not action_ids:
        return set()
    return set(Action.objects.filter(id__in=action_ids).values_list("id", flat=True))
