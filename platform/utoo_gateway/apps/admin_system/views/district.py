from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import district as district_repo
from apps.admin_system.views.common import merge_payload


def _district_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "super_id": data.get("superId") or data.get("super_id") or "0",
        "dis_sort": int(data.get("disSort") or data.get("dis_sort") or 0),
        "dis_name": (data.get("disName") or data.get("dis_name") or "").strip(),
        "dis_desc": data.get("disDesc") or data.get("dis_desc"),
        "type": data.get("type"),
        "area_id": data.get("areaId") or data.get("area_id"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def district_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = district_repo.list_districts(
        super_id=str(data.get("superId") or data.get("super_id") or ""),
        dis_name=(data.get("disName") or data.get("dis_name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def district_children(request: Request, user=None):
    del user
    data = merge_payload(request)
    super_id = data.get("superId") or data.get("super_id") or "0"
    return ajax_response(True, obj=district_repo.list_children(str(super_id)))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def district_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _district_payload(data)
    if not payload["dis_name"]:
        return Response(False)
    district_repo.insert_district(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def district_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _district_payload(data)
    if not payload["id"] or not payload["dis_name"]:
        return Response(False)
    district_repo.update_district(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def district_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    ids = data.get("ids")
    if ids:
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        for district_id in ids:
            if district_id:
                district_repo.delete_district(str(district_id))
        return Response(True)
    district_id = data.get("id")
    if not district_id:
        return Response(False)
    district_repo.delete_district(str(district_id))
    return Response(True)
