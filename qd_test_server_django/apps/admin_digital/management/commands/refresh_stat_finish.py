"""手工补刷数字化统计快照表（对齐 Java 凌晨定时任务）。

用法:
  python manage.py refresh_stat_finish
  python manage.py refresh_stat_finish --finish-only
  python manage.py refresh_stat_finish --lines-only
  python manage.py refresh_stat_finish --users-only
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.admin_digital.repositories import finish_sync


class Command(BaseCommand):
    help = "刷新 statistic_experiment_finish / 实验线 run_num / 人员 test_num（停 Java 后需定时或手工执行）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--finish-only",
            action="store_true",
            help="仅重刷 statistic_experiment_finish",
        )
        parser.add_argument(
            "--lines-only",
            action="store_true",
            help="仅刷新 experiment_line.run_num",
        )
        parser.add_argument(
            "--users-only",
            action="store_true",
            help="仅刷新 sy_users.test_num",
        )

    def handle(self, *args, **options):
        finish_only = options["finish_only"]
        lines_only = options["lines_only"]
        users_only = options["users_only"]
        exclusive = sum(1 for x in (finish_only, lines_only, users_only) if x)

        if exclusive == 0:
            result = finish_sync.refresh_all_stat_snapshots()
            self.stdout.write(self.style.SUCCESS(f"全量刷表完成: {result}"))
            return

        if finish_only:
            result = finish_sync.refresh_statistic_finish()
            self.stdout.write(self.style.SUCCESS(f"finish 完成: {result}"))
        if lines_only:
            result = finish_sync.refresh_line_run_num()
            self.stdout.write(self.style.SUCCESS(f"lines 完成: {result}"))
        if users_only:
            result = finish_sync.refresh_user_test_num()
            self.stdout.write(self.style.SUCCESS(f"users 完成: {result}"))
