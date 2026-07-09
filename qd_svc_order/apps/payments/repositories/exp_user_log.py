from apps.core.db_utils import execute


def save_exp_user_log(user_id: int, info: str) -> None:
    try:
        execute(
            """
            INSERT INTO exp_user_log (addTime, deleteStatus, user_id, info)
            VALUES (NOW(), 0, %(uid)s, %(info)s)
            """,
            {"uid": user_id, "info": info},
        )
    except Exception:
        pass
