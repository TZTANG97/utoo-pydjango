from apps.wx.repositories import feedback as feedback_repo


def add_feedback(*, user_id: int, content: str) -> tuple[bool, str]:
    if not content or not str(content).strip():
        return False, "请填写反馈内容"
    feedback_repo.insert_feedback(user_id=user_id, content=content.strip())
    return True, "意见反馈成功"
