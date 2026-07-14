def is_sy_staff(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("account_kind") == "sy_user":
        return True
    return str(user.get("user_type")) != "1" and user.get("account_kind") != "exp_user"
