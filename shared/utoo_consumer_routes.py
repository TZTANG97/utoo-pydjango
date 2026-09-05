"""C 端 / 小程序 / 登录路径 → 中台或网关 internal 回退。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MidTarget(str, Enum):
    ORDER = "order"
    PAYMENT = "payment"
    PLATFORM = "platform"
    IDENTITY = "identity"
    GATEWAY_INTERNAL = "gateway_internal"
    # utoo_biz 已本地挂载；若仍走 proxy 应 503，禁止 silent twin
    BIZ_LOCAL = "biz_local"


@dataclass(frozen=True)
class RouteDecision:
    target: MidTarget
    channel: str
    path: str


_PC_PAYMENT = frozenset(
    {
        "getIntegral.ajax",
        "getIntegralConvertRatio.ajax",
        "center/getAccount.ajax",
        "center/getIntegralList.ajax",
        "selRechargeStatus.ajax",
        "selRechargeList.ajax",
        "selDefaultAccount.ajax",
        "amountPay.ajax",
        "prePay.ajax",
        "preAmountPay.ajax",
        "rechargePrePay.ajax",
        "rechargeContinuePay.ajax",
        "addRecharge.ajax",
        "addCash.ajax",
        "saveaccessory.ajax",
        "queryPayStatus.ajax",
        "queryPayStatusByOrder.ajax",
        "pay.ajax",
        "rechargePay.ajax",
        "amountPayBack.ajax",
    }
)

_PC_PLATFORM = frozenset(
    {
        "center/getInvoiceList.ajax",
        "center/getInvoiceOrderList.ajax",
        "center/applyInvoice.ajax",
        "center/getInvoiceLogList.ajax",
        "center/getInvoiceInfo.ajax",
        "getinvoiceInfo.ajax",
        "insertinvoiceInfo.ajax",
        "updateinvoiceInfo.ajax",
        "delinvoiceInfo.ajax",
        "addInvoiceInfo.ajax",
        "cancelInvoiceInfo.ajax",
    }
)

# C 端会员凭证 / 主数据（identity 基础能力；禁止产品编排）
_PC_IDENTITY = frozenset(
    {
        "register.ajax",
        "getVerifyCode.ajax",
        "getVerifyCodeFindPw.ajax",
        "telCodeVerify.ajax",
        "getUserBasicInfo.ajax",
        "updateUserBasicInfo.ajax",
        "setPassword.ajax",
        "updatePhone.ajax",
        "addOrUpdateUserData.ajax",
        "addOrUpdateUserCompanyData.ajax",
    }
)

_PC_ORDER = frozenset(
    {
        "indexClassList.ajax",
        "bannerList.ajax",
        "getXcxBanner.ajax",
        "getTuZheBanner.ajax",
        "selThirdClassList.ajax",
        "selFirAndSecClassList.ajax",
        "selThirdClassByKeyWordList.ajax",
        "indexExpList.ajax",
        "selExpList.ajax",
        "testClassDetail.ajax",
        "xcxtestClassDetail.ajax",
        "useraddress.ajax",
        "getdeliveryaddress.ajax",
        "insertdeliveryaddress.ajax",
        "updatedeliveryaddress.ajax",
        "deldeliveryaddress.ajax",
        "selCompanyName.ajax",
        "center/getOrderData.ajax",
        "myExperimentOrderList.ajax",
        "experimentOrderList.ajax",
        "selTestOrSure.ajax",
        "queryProCityCo.ajax",
        "queryProCityCo1.ajax",
        "writeevaluate.ajax",
        "serviceConsultAdd.ajax",
        "expMakeList.ajax",
        "myExpMakeList.ajax",
        "myExpMakeStatusList.ajax",
        "saveServiceConsult.ajax",
        "cancelConsult.ajax",
        "printYyd.ajax",
        "downloadFile.ajax",
    }
)

# 小程序路径 → 等价 /api/pc/ 路径（与 utoo_gateway wx_mp 别名表一致）
_WX_PC_ALIAS: dict[str, str] = {
    "addOrUpdateUserData.ajax": "addOrUpdateUserData.ajax",
    "addOrUpdateUserCompanyData.ajax": "addOrUpdateUserCompanyData.ajax",
    "serviceConsultAdd.ajax": "serviceConsultAdd.ajax",
    "expMakeList.ajax": "expMakeList.ajax",
    "myExperimentOrderList.ajax": "myExperimentOrderList.ajax",
    "amountPay.ajax": "amountPay.ajax",
    "prePay.ajax": "prePay.ajax",
    "preAmountPay.ajax": "preAmountPay.ajax",
    "rechargePrePay.ajax": "rechargePrePay.ajax",
    "addRecharge.ajax": "addRecharge.ajax",
    "addCash.ajax": "addCash.ajax",
    "pay.ajax": "pay.ajax",
    "center/getAccount.ajax": "center/getAccount.ajax",
    "center/getIntegralList.ajax": "center/getIntegralList.ajax",
    "center/getInvoiceInfo.ajax": "center/getInvoiceInfo.ajax",
    "center/applyInvoice.ajax": "center/applyInvoice.ajax",
    "getinvoiceInfo.ajax": "getinvoiceInfo.ajax",
    "insertinvoiceInfo.ajax": "insertinvoiceInfo.ajax",
    "updateinvoiceInfo.ajax": "updateinvoiceInfo.ajax",
    "delinvoiceInfo.ajax": "delinvoiceInfo.ajax",
    "addInvoiceInfo.ajax": "addInvoiceInfo.ajax",
    "setPassword.ajax": "setPassword.ajax",
    "telCodeVerify.ajax": "telCodeVerify.ajax",
    "getVerifyCodeFindPw.ajax": "getVerifyCodeFindPw.ajax",
    "writeevaluate.ajax": "writeevaluate.ajax",
    "bannerList.ajax": "bannerList.ajax",
    "selFirAndSecClassList.ajax": "selFirAndSecClassList.ajax",
}

# 小程序独有路径 → 中台（保持 /api/wx/{sub}，禁止回落 _internal）
# 仓扫 scanCodeOperate/isFlag 写实验单 → order；微信登录 QR 令牌 / 补资料 → payment
_WX_MID: dict[str, MidTarget] = {
    "getVerifyCodeLogin.ajax": MidTarget.IDENTITY,
    "userLoginToken.ajax": MidTarget.IDENTITY,
    "phoneCodeLogin.ajax": MidTarget.IDENTITY,
    "phoneOneLogin.ajax": MidTarget.IDENTITY,
    "phoneOneLoginTZ.ajax": MidTarget.IDENTITY,
    "getIdentifyData.ajax": MidTarget.IDENTITY,
    "clearBindData.ajax": MidTarget.IDENTITY,
    "myInfo.ajax": MidTarget.IDENTITY,
    "getbindstatus.ajax": MidTarget.IDENTITY,
    "checkLoginName.ajax": MidTarget.IDENTITY,
    "updateNickName.ajax": MidTarget.IDENTITY,
    "TuZhebannerList.ajax": MidTarget.ORDER,
    "selFirAndSecClassListTuZhe.ajax": MidTarget.ORDER,
    "getOrderCount.ajax": MidTarget.ORDER,
    "scanCodeOperate.ajax": MidTarget.ORDER,
    "isFlag.ajax": MidTarget.ORDER,
    # QR 补资料：ticket Redis 与 WeChatQRCodeGenerator / qrScanStatusCheck 同进程
    "getUserInfo.ajax": MidTarget.PAYMENT,
    "userInfoAdd.ajax": MidTarget.PAYMENT,
    "ticketIsExist.ajax": MidTarget.PAYMENT,
}

# 仍 twin / stub：未实现接口（保持 _internal → 501 stub；勿误迁中台）
_WX_STUBS = frozenset(
    {
        "bindaccount.ajax",
        "bindaccountTZ.ajax",
        "securebind.ajax",
        "getAuditOrderList.ajax",
        "getAuditOrderList1.ajax",
        "getLog.ajax",
        "selBankList.ajax",
        "selSecondClassList.ajax",
        "signInIntegral.ajax",
    }
)

_IDENTITY_AUTH = {
    "login": "/api/v1/identity/auth/login",
    "refresh": "/api/v1/identity/auth/refresh",
    "me": "/api/v1/identity/auth/me",
}

# 后台咨询管理（写权在 admin_platform）；须与 gateway _ADMIN_PLATFORM_EXACT 对齐
_CONSULT_PLATFORM = frozenset(
    {
        "list.ajax",
        "consultDetail.ajax",
        "consultDetailxq.ajax",
        "cancelConsult.ajax",
        "updateConsult.ajax",
        "saveOrder.ajax",
        "querySampleList.ajax",
        "settingGet.ajax",
        "settingSave.ajax",
        "isshowGet.ajax",
        "isshowSave.ajax",
        "consultConfigGet.ajax",
        "consultConfigSave.ajax",
    }
)


def _pc_subpath(full_path: str) -> str:
    p = full_path.split("?", 1)[0]
    if p.startswith("/api/pc/"):
        return p[len("/api/pc/") :]
    return ""


def _wx_subpath(full_path: str) -> str:
    p = full_path.split("?", 1)[0]
    if p.startswith("/api/wx/"):
        return p[len("/api/wx/") :]
    return ""


def _resolve_pc_subpath(sub: str, *, channel: str) -> RouteDecision:
    pc_path = f"/api/pc/{sub}"
    if sub in _PC_PAYMENT:
        return RouteDecision(MidTarget.PAYMENT, channel, pc_path)
    if sub in _PC_PLATFORM:
        return RouteDecision(MidTarget.PLATFORM, channel, pc_path)
    if sub in _PC_ORDER:
        return RouteDecision(MidTarget.ORDER, channel, pc_path)
    if sub in _PC_IDENTITY:
        return RouteDecision(MidTarget.IDENTITY, channel, pc_path)
    return RouteDecision(
        MidTarget.GATEWAY_INTERNAL,
        channel,
        f"/api/_internal/pc/{sub}",
    )


def resolve_consumer_path(full_path: str) -> RouteDecision:
    path = full_path.split("?", 1)[0]

    if path.startswith("/api/auth/"):
        action = path[len("/api/auth/") :].strip("/")
        identity_path = _IDENTITY_AUTH.get(action)
        if identity_path:
            return RouteDecision(MidTarget.IDENTITY, "pc", identity_path)
        return RouteDecision(
            MidTarget.GATEWAY_INTERNAL,
            "pc",
            path.replace("/api/auth/", "/api/_internal/auth/", 1),
        )

    if path.startswith("/api/consult/"):
        sub = path[len("/api/consult/") :].split("?", 1)[0]
        if sub in _CONSULT_PLATFORM:
            return RouteDecision(MidTarget.PLATFORM, "admin", path)
        # C 端 isServiceConsult 等 → order 中台（禁止回落 gateway twin）
        return RouteDecision(MidTarget.ORDER, "pc", path)

    if path == "/api/index/userRoles.ajax":
        return RouteDecision(MidTarget.BIZ_LOCAL, "wx", path)

    if path.startswith("/api/pc/"):
        sub = _pc_subpath(path)
        return _resolve_pc_subpath(sub, channel="pc")

    if path.startswith("/api/wx/"):
        sub = _wx_subpath(path)
        # wechatconfig 由网关本地承接，不经 biz resolve
        if sub == "wechatconfig.ajax":
            return RouteDecision(MidTarget.GATEWAY_INTERNAL, "wx", path)
        if sub in _WX_PC_ALIAS:
            return _resolve_pc_subpath(_WX_PC_ALIAS[sub], channel="wx")
        mid = _WX_MID.get(sub)
        if mid is not None:
            return RouteDecision(mid, "wx", f"/api/wx/{sub}")
        # 未实现 stubs（见 _WX_STUBS）仍 twin → 501
        return RouteDecision(
            MidTarget.GATEWAY_INTERNAL,
            "wx",
            f"/api/_internal/wx/{sub}",
        )

    return RouteDecision(MidTarget.GATEWAY_INTERNAL, "pc", path)
