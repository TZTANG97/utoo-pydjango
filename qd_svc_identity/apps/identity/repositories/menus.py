from apps.identity.models import Menu, RoleMenu


def list_all_rows(*, pt_type: str):
    return list(
        Menu.objects.filter(pt_type__contains=pt_type)
        .order_by("menu_sort", "id")
        .values(
            "id",
            "menu_super_id",
            "menu_status",
            "menu_sort",
            "menu_name",
            "menu_icon",
            "menu_url",
            "menu_target",
            "menu_rel",
            "pt_type",
        )
    )


def get_platform_by_id(menu_id, pt_type: str):
    return Menu.objects.filter(id=menu_id, pt_type__contains=pt_type).first()


def menu_name_exists(menu_name, menu_super_id, *, exclude_id=None, pt_type: str):
    rows = Menu.objects.filter(
        menu_name=menu_name,
        menu_super_id=menu_super_id or None,
        pt_type__contains=pt_type,
    )
    if exclude_id:
        rows = rows.exclude(id=exclude_id)
    return rows.exists()


def has_children(menu_id):
    return Menu.objects.filter(menu_super_id=menu_id).exists()


def save_menu(menu, *, update_fields=None):
    if update_fields is not None:
        menu.save(update_fields=update_fields)
    else:
        menu.save()
    return menu


def delete_menu(menu):
    menu.delete()


def delete_role_menus_for_menu(menu_id):
    RoleMenu.objects.filter(menu_id=menu_id).delete()
