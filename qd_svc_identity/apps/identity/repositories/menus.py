from apps.identity.models import Menu, RoleMenu


def list_all_rows():
    """菜单管理对齐 Java queryMenus：全表 sy_menu，不按 pt_type 裁。"""
    return list(
        Menu.objects.order_by("menu_sort", "id")
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
            "menu_open",
            "menu_external",
            "menu_fresh",
            "pt_type",
        )
    )


def get_by_id(menu_id):
    if str(menu_id or "") in {"", "0"}:
        return None
    return Menu.objects.filter(id=menu_id).first()


def get_platform_by_id(menu_id, pt_type: str):
    if str(menu_id or "") in {"", "0"}:
        return None
    return Menu.objects.filter(id=menu_id, pt_type__contains=pt_type).first()


def menu_name_exists(menu_name, menu_super_id, *, exclude_id=None):
    rows = Menu.objects.filter(
        menu_name=menu_name,
        menu_super_id=menu_super_id or None,
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
