from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.authentication import IdentityJWTAuthentication, TokenUser
from apps.identity.channel import ChannelError, channel_from_request
from apps.identity.services import org as org_svc


def _tree(rows, parent_key):
    children_by_parent = {}
    ids = {row["id"] for row in rows}
    for row in rows:
        children_by_parent.setdefault(row[parent_key] or "", []).append(row)

    def build(parent_id):
        nodes = []
        for row in children_by_parent.get(parent_id or "", []):
            node = dict(row)
            node["children"] = build(row["id"])
            nodes.append(node)
        return nodes

    roots = [row for row in rows if not row[parent_key] or row[parent_key] not in ids]
    return [dict(row, children=build(row["id"])) for row in roots]


class OrgJwtView(APIView):
    """青岛/UTOO 员工组织写：对齐 mall identity views，仅 staff 渠道。"""

    authentication_classes = [IdentityJWTAuthentication]
    permission_classes = [AllowAny]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        try:
            ctx = channel_from_request(request)
        except ChannelError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        if ctx.account_kind != "sy_user" or not ctx.platform:
            raise PermissionDenied("当前渠道不支持组织管理")
        if not isinstance(getattr(request, "user", None), TokenUser):
            raise AuthenticationFailed("缺少 Bearer JWT")
        self.claims = request.user._payload
        self.platform = str(ctx.platform)
        self.role_type = int(ctx.platform)

    def actor_id(self):
        return str(self.claims.get("sub") or self.claims.get("user_id") or "")


class DepartmentTreeView(OrgJwtView):
    def get(self, _request):
        return Response({"data": _tree(org_svc.list_department_rows(), "super_id")})

    def post(self, request):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/dept/add.do")
        return Response({"data": org_svc.create_department(request.data)}, status=status.HTTP_201_CREATED)


class DepartmentDetailView(OrgJwtView):
    def patch(self, request, dept_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/dept/update.do")
        return Response({"data": org_svc.update_department(dept_id, request.data)})

    def delete(self, _request, dept_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/dept/del.do")
        org_svc.delete_department(dept_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(OrgJwtView):
    def get(self, request):
        keyword = request.query_params.get("keyword", "").strip()
        return Response({"data": org_svc.list_roles(keyword=keyword, role_type=self.role_type)})

    def post(self, request):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/role/add.do")
        return Response(
            {"data": org_svc.create_role(request.data, role_type=self.role_type)},
            status=status.HTTP_201_CREATED,
        )


class RoleDetailView(OrgJwtView):
    def get(self, _request, role_id):
        role = org_svc.get_role(role_id, role_type=self.role_type)
        return Response(
            {
                "data": org_svc.serialize_role(
                    role,
                    menu_ids=org_svc.role_menu_ids(role.id),
                    action_ids=org_svc.role_action_ids(role.id),
                )
            }
        )

    def patch(self, request, role_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/role/update.do")
        return Response({"data": org_svc.update_role(role_id, request.data, role_type=self.role_type)})

    def delete(self, _request, role_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/role/del.do")
        org_svc.delete_role(role_id, role_type=self.role_type)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleMenuView(OrgJwtView):
    def put(self, request, role_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/role/power/update.do")
        menu_ids = org_svc.id_list(request.data.get("menu_ids") if isinstance(request.data, dict) else None, "menu_ids")
        return Response(
            {
                "data": {
                    "menu_ids": org_svc.replace_role_menus(
                        role_id, menu_ids, role_type=self.role_type, pt_type=self.platform
                    )
                }
            }
        )


class RoleActionView(OrgJwtView):
    def put(self, request, role_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/role/power/update.do")
        action_ids = org_svc.id_list(
            request.data.get("action_ids") if isinstance(request.data, dict) else None, "action_ids"
        )
        return Response(
            {"data": {"action_ids": org_svc.replace_role_actions(role_id, action_ids, role_type=self.role_type)}}
        )


class UserListView(OrgJwtView):
    def get(self, request):
        keyword = request.query_params.get("keyword", "").strip()
        include_disabled = (request.query_params.get("include_disabled") or "").lower() in {"1", "true", "yes"}
        return Response(
            {
                "data": org_svc.list_admin_users(
                    keyword=keyword, include_disabled=include_disabled, pt_type=self.platform
                )
            }
        )

    def post(self, request):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/add.do")
        return Response(
            {"data": org_svc.create_user(request.data, pt_type=self.platform, role_type=self.role_type)},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(OrgJwtView):
    def get(self, _request, user_id):
        user = org_svc.get_user(user_id)
        return Response({"data": org_svc.serialize_user(user, role_ids=org_svc.user_role_ids(user.id))})

    def patch(self, request, user_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/update.do")
        return Response({"data": org_svc.update_user(user_id, request.data)})


class UserRoleView(OrgJwtView):
    def put(self, request, user_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/updateRole.do")
        org_svc.get_user(user_id)
        role_ids = org_svc.id_list(request.data.get("role_ids") if isinstance(request.data, dict) else None, "role_ids")
        return Response(
            {"data": {"role_ids": org_svc.replace_user_roles(user_id, role_ids, role_type=self.role_type)}}
        )


class ChangeMyPasswordView(OrgJwtView):
    def post(self, request):
        org_svc.require_write_enabled()
        return Response({"data": org_svc.change_my_password(self.actor_id(), request.data)})


class DataScopeView(OrgJwtView):
    def get(self, _request, user_id=None):
        target_id = user_id or self.actor_id()
        if user_id and user_id != self.actor_id() and (self.claims.get("scope") or {}).get("filter_list") != 2:
            raise PermissionDenied("只能查看自己的数据范围")
        return Response({"data": org_svc.get_data_scope(target_id, pt_type=self.platform)})


class UserPasswordView(OrgJwtView):
    def post(self, request, user_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/update.do")
        return Response({"data": org_svc.reset_user_password(user_id, request.data)})


class UserAccessView(OrgJwtView):
    def get(self, _request, user_id):
        return Response({"data": org_svc.get_user_access(user_id, pt_type=self.platform)})

    def put(self, request, user_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/updateAccessRights.do")
        return Response({"data": org_svc.replace_user_access(user_id, request.data, pt_type=self.platform)})


class UserStatusView(OrgJwtView):
    def post(self, request, user_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/user/del.do", "/sys/user/update.do")
        payload = request.data if isinstance(request.data, dict) else {}
        try:
            user_status = int(payload.get("user_status"))
        except (TypeError, ValueError):
            raise ValidationError({"user_status": "必须是 0 或 1"})
        return Response({"data": org_svc.set_user_status(user_id, user_status, actor_id=self.actor_id())})


class MenuAdminTreeView(OrgJwtView):
    def get(self, _request):
        return Response({"data": _tree(org_svc.list_all_menu_rows(pt_type=self.platform), "menu_super_id")})


class MenuCreateView(OrgJwtView):
    def post(self, request):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/menu/add.do")
        return Response(
            {"data": org_svc.create_menu(request.data, pt_type=self.platform)},
            status=status.HTTP_201_CREATED,
        )


class MenuDetailView(OrgJwtView):
    def get(self, _request, menu_id):
        return Response({"data": org_svc.serialize_menu(org_svc.get_menu(menu_id, pt_type=self.platform))})

    def patch(self, request, menu_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/menu/update.do")
        return Response({"data": org_svc.update_menu(menu_id, request.data, pt_type=self.platform)})

    def delete(self, _request, menu_id):
        org_svc.require_write_enabled()
        org_svc.require_legacy_permission(self.claims, "/sys/menu/del.do")
        org_svc.delete_menu(menu_id, pt_type=self.platform)
        return Response(status=status.HTTP_204_NO_CONTENT)
