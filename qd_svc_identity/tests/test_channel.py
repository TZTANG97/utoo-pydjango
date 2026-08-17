import pytest

from apps.identity.channel import ChannelError, resolve_channel


def test_mall_qd_staff_platform_1():
    ctx = resolve_channel("mall_qd")
    assert ctx.account_kind == "sy_user"
    assert ctx.platform == "1"
    assert ctx.returns_admin_menus is True


def test_admin_staff_platform_2():
    ctx = resolve_channel("admin")
    assert ctx.account_kind == "sy_user"
    assert ctx.platform == "2"
    assert ctx.returns_admin_menus is True


def test_pc_wx_customer_no_admin_menus():
    for ch in ("pc", "wx", "PC", " Wx "):
        ctx = resolve_channel(ch)
        assert ctx.account_kind == "exp_user"
        assert ctx.platform is None
        assert ctx.returns_admin_menus is False


def test_factory_rejected_phase1():
    with pytest.raises(ChannelError, match="一期不含工厂"):
        resolve_channel("emku")
    with pytest.raises(ChannelError, match="一期不含工厂"):
        resolve_channel("factory")


def test_missing_and_unknown():
    with pytest.raises(ChannelError, match="缺少"):
        resolve_channel("")
    with pytest.raises(ChannelError, match="不支持"):
        resolve_channel("iot")
