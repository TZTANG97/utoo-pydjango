from celery import shared_task


@shared_task(name="tasks.ping")
def ping() -> str:
    """Celery 连通性探测（D0）"""
    return "pong"


@shared_task(name="tasks.refresh_statistic_experiment_finish")
def refresh_statistic_experiment_finish() -> dict:
    """对齐 Java OrderTimeoutTaskAction#integralEarnings2：全量重刷 statistic_experiment_finish。"""
    from apps.admin_digital.repositories import finish_sync

    return finish_sync.refresh_statistic_finish()


@shared_task(name="tasks.refresh_stat_line_run_num")
def refresh_stat_line_run_num() -> dict:
    """对齐 integralEarnings5。"""
    from apps.admin_digital.repositories import finish_sync

    return finish_sync.refresh_line_run_num()


@shared_task(name="tasks.refresh_stat_user_test_num")
def refresh_stat_user_test_num() -> dict:
    """对齐 integralEarnings6。"""
    from apps.admin_digital.repositories import finish_sync

    return finish_sync.refresh_user_test_num()


@shared_task(name="tasks.refresh_all_stat_snapshots")
def refresh_all_stat_snapshots() -> dict:
    """统计页相关三件套：finish + 实验线 + 人员 test_num。"""
    from apps.admin_digital.repositories import finish_sync

    return finish_sync.refresh_all_stat_snapshots()
