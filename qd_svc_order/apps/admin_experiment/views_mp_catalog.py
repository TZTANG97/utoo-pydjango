"""小程序 Java 路径别名：experimentManage / experimentProject / experimentGoods。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import (
    datatable_payload,
    merge_payload,
    parse_datatable_params,
    to_int,
)
from apps.admin_experiment.repositories import master as master_repo
from qd_common.responses import ajax_fail, ajax_ok
from qd_common.serialize import to_jsonable


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def manage_query_all(request: Request):
    """experimentManage/queryAll.ajax?type=1|2|3"""
    data = merge_payload(request)
    type_ = to_int(data.get("type"), 0) or 0
    if type_ not in (1, 2, 3):
        return Response(ajax_fail("参数错误,请重试"))
    rows = master_repo.query_all_manages(type_)
    return Response(ajax_ok(obj=to_jsonable(rows), res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def manage_query_by_parent(request: Request):
    """experimentManage/queryByParentId.ajax"""
    data = merge_payload(request)
    parent_id = to_int(data.get("parent_id") or data.get("parentId"), 0) or 0
    if not parent_id:
        return Response(ajax_fail("参数错误"))
    rows = master_repo.list_manages_by_parent(parent_id)
    return Response(ajax_ok(obj=to_jsonable(rows), res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def project_list_java(request: Request):
    """experimentProject/list.ajax — DataTables，字段对齐小程序。"""
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = master_repo.list_projects(
        name=str(data.get("project_name") or data.get("projectName") or data.get("name") or "").strip(),
        first_id=str(data.get("first_id") or data.get("firstId") or "").strip(),
        sec_id=str(data.get("sec_id") or data.get("secId") or "").strip(),
        third_id=str(
            data.get("class_id") or data.get("classId") or data.get("third_id") or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    out = []
    for r in rows:
        out.append(
            {
                "id": r.get("id"),
                "project_name": r.get("projectName") or r.get("project_name") or "",
                "class_name": r.get("className") or r.get("class_name") or "",
                "class_id": r.get("classId") or r.get("class_id"),
                "sec_name": r.get("secName") or "",
                "first_name": r.get("firstName") or "",
                "addTime": r.get("addTime"),
            }
        )
    return Response(datatable_payload(draw=draw, total=total, rows=to_jsonable(out)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def goods_list_java(request: Request):
    """experimentGoods/list.ajax — DataTables。"""
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = master_repo.list_goods(
        name=str(
            data.get("goods_name") or data.get("goodsName") or data.get("name") or ""
        ).strip(),
        brand_id=str(
            data.get("goods_brand_id") or data.get("brandId") or data.get("brand_id") or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    out = []
    for r in rows:
        out.append(
            {
                "id": r.get("id"),
                "goods_name": r.get("goodsName") or r.get("goods_name") or "",
                "goods_model": r.get("goodsModel") or r.get("goods_model") or "",
                "goods_brand_id": r.get("brandId") or r.get("goods_brand_id"),
                "brand_name": r.get("brandName") or "",
                "addTime": r.get("addTime"),
            }
        )
    return Response(datatable_payload(draw=draw, total=total, rows=to_jsonable(out)))
