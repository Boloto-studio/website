from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from django.utils.timezone import now
        from .jobs import poll_youtube, delete_old_job_executions

        # Or use 'America/New_York', etc.
        scheduler = BackgroundScheduler(timezone='UTC')
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            poll_youtube,
            trigger='interval',
            hours=1,
            id='youtube_polling_job',
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            delete_old_job_executions,
            trigger='cron',
            day_of_week='mon',
            hour=0,
            minute=0,
            id='delete_old_job_executions',
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Scheduler started...")
