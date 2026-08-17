from apps.identity.services.menus import filter_menus_by_platform, filter_roles_by_type


def test_same_user_menus_not_cross_platform():
    """同账号若挂了多平台菜单，mall_qd(1) 与 admin(2) 投影不得串。"""
    mixed = [
        {"id": "a", "menu_name": "大平台系统", "pt_type": "1"},
        {"id": "b", "menu_name": "UTOO运营", "pt_type": "2"},
        {"id": "c", "menu_name": "双挂", "pt_type": "1,2"},
        {"id": "d", "menu_name": "工厂仓储", "pt_type": "3"},
    ]
    mall = {m["id"] for m in filter_menus_by_platform(mixed, "1")}
    admin = {m["id"] for m in filter_menus_by_platform(mixed, "2")}
    assert mall == {"a", "c"}
    assert admin == {"b", "c"}
    assert "d" not in mall
    assert "d" not in admin
    assert mall & admin == {"c"}


def test_role_type_filter():
    roles = [
        {"id": 1, "type": 1},
        {"id": 2, "type": 2},
        {"id": 3, "type": 3},
    ]
    assert [r["id"] for r in filter_roles_by_type(roles, 1)] == [1]
    assert [r["id"] for r in filter_roles_by_type(roles, "2")] == [2]
