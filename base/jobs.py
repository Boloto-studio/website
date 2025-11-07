from django_apscheduler.models import DjangoJobExecution
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


def poll_youtube():
    """Sync YouTube livestreams with Event model"""
    logger.info("Starting YouTube sync...")
    try:
        call_command('sync_youtube')
        logger.info("YouTube sync completed successfully")
    except Exception as e:
        logger.error(f"YouTube sync failed: {str(e)}")


def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
