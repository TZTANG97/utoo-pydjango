from apps.identity.models import UserCompanyLink, UserOrderTypeLink, UserSalesLink


def list_company_ids(user_id, pt_type: str):
    return list(
        UserCompanyLink.objects.filter(
            user_id=user_id,
            delete_status=False,
            pt_type__contains=pt_type,
        ).values_list("company_id", flat=True)
    )


def list_order_type_ids(user_id, pt_type: str):
    return list(
        UserOrderTypeLink.objects.filter(
            user_id=user_id,
            delete_status=False,
            pt_type__contains=pt_type,
        ).values_list("type_id", flat=True)
    )


def list_saleuser_ids(user_id, pt_type: str):
    return list(
        UserSalesLink.objects.filter(
            user_id=user_id,
            delete_status=False,
            pt_type__contains=pt_type,
        ).values_list("saleuser_id", flat=True)
    )


def soft_delete_company_links(user_id, pt_type: str):
    UserCompanyLink.objects.filter(
        user_id=user_id,
        delete_status=False,
        pt_type__contains=pt_type,
    ).update(delete_status=True)


def soft_delete_order_type_links(user_id, pt_type: str):
    UserOrderTypeLink.objects.filter(
        user_id=user_id,
        delete_status=False,
        pt_type__contains=pt_type,
    ).update(delete_status=True)


def soft_delete_saleuser_links(user_id, pt_type: str):
    UserSalesLink.objects.filter(
        user_id=user_id,
        delete_status=False,
        pt_type__contains=pt_type,
    ).update(delete_status=True)


def bulk_create_company_links(rows):
    UserCompanyLink.objects.bulk_create(rows)


def bulk_create_order_type_links(rows):
    UserOrderTypeLink.objects.bulk_create(rows)


def bulk_create_saleuser_links(rows):
    UserSalesLink.objects.bulk_create(rows)
