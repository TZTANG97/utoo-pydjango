from celery import shared_task


@shared_task(name="tasks.ping")
def ping() -> str:
    """Celery 连通性探测（D0）"""
    return "pong"
