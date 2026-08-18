from apps.identity.services.menus import (
    filter_menus_by_platform,
    filter_roles_by_type,
    serialize_java_top_menu,
    serialize_sy_menu_map,
)


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


def test_query_menus_match_java_sy_menu_fields():
    row = serialize_sy_menu_map(
        {
            "id": "0",
            "menu_super_id": "0",
            "menu_status": 1,
            "menu_sort": 0,
            "menu_name": "系统菜单",
            "menu_icon": "icon.png",
            "menu_url": "",
            "menu_target": "navTab",
            "menu_rel": "sys",
            "menu_open": "true",
            "menu_external": "false",
            "menu_fresh": "true",
        }
    )
    assert set(row) == {
        "id",
        "menuSuperId",
        "menuStatus",
        "menuSort",
        "menuName",
        "menuIcon",
        "menuUrl",
        "menuTarget",
        "menuRel",
        "menuOpen",
        "menuExternal",
        "menuFresh",
    }
    assert row["menuName"] == "系统菜单"
    assert row["menuSuperId"] == "0"


def test_login_menus_match_java_select_menus_top():
    tops = [
        {
            "id": "sales",
            "menu_name": "销售管理",
            "menu_super_id": "0",
            "menu_icon": "sales.png",
            "menu_url": "",
            "menu_target": "navTab",
            "menu_rel": "sales",
            "menu_open": "true",
            "menu_external": "false",
            "menu_fresh": "true",
        }
    ]
    all_menus = tops + [
        {
            "id": "order",
            "menu_name": "订单列表",
            "menu_super_id": "sales",
            "menu_icon": "order.png",
            "menu_url": "/saleOrder/load.do",
            "menu_target": "navTab",
            "menu_rel": "order",
            "menu_open": "false",
            "menu_external": "false",
            "menu_fresh": "true",
        }
    ]
    top = serialize_java_top_menu(tops[0], all_menus)
    assert top["menuName"] == "销售管理"
    assert top["pid"] == "0"
    assert top["icon"] == "sales.png"
    assert "childMenu" in top
    child = top["childMenu"][0]
    assert child["name"] == "订单列表"
    assert child["url"] == "/saleOrder/load.do"
    assert child["superId"] == "sales"
    assert child["childrenMenus"] == []
