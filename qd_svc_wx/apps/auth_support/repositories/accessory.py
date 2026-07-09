from apps.core.db_utils import execute_insert


def insert_avatar_row(*, add_time, filename: str, path: str, content_type: str) -> int:
    return execute_insert(
        """
        INSERT INTO accessory
            (addTime, deleteStatus, name, path, ext, width, height)
        VALUES (%(t)s, 0, %(name)s, %(path)s, %(ext)s, 0, 0)
        """,
        {
            "t": add_time,
            "name": filename,
            "path": path,
            "ext": content_type,
        },
    )
