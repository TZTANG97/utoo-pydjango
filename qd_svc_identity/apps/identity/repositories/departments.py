from apps.identity.models import Department


def list_tree_rows():
    return list(
        Department.objects.order_by("dept_sort", "id").values(
            "id", "super_id", "dept_name", "dept_phone", "lead_uid", "dept_desc"
        )
    )


def get_by_id(dept_id):
    return Department.objects.filter(id=dept_id).first()


def has_children(dept_id):
    return Department.objects.filter(super_id=dept_id).exists()


def save_department(dept, *, update_fields=None):
    if update_fields is not None:
        dept.save(update_fields=update_fields)
    else:
        dept.save()
    return dept


def delete_department(dept):
    dept.delete()
