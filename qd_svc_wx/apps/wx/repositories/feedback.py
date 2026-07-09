from apps.core.db_utils import execute_insert


def insert_feedback(*, user_id: int, content: str) -> int:
    return execute_insert(
        """
        INSERT INTO exp_feedback (addTime, deleteStatus, user_id, content)
        VALUES (NOW(), 0, %(uid)s, %(content)s)
        """,
        {"uid": user_id, "content": content},
    )
