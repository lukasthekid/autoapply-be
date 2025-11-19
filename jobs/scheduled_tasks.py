"""
Scheduled tasks for the jobs app.

This module contains scheduled tasks similar to Spring Boot's @Scheduled annotation.
Tasks are automatically registered when Django starts.

Example:
    @scheduler.scheduled_job('cron', hour=0, minute=0)  # Run at midnight
    def cleanup_unused_jobs():
        # Your task code here
        pass
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution
from django.core.management import call_command
from django_apscheduler import util
import logging

logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


@scheduler.scheduled_job(
    trigger=CronTrigger(hour=0, minute=0),  # Run every day at midnight
    id="cleanup_unused_jobs",
    name="Cleanup unused job listings",
    replace_existing=True,
    max_instances=1,
)
@util.close_old_connections
def cleanup_unused_jobs():
    """
    Scheduled task to delete job listings that have no applications.
    
    This task runs every day at midnight (00:00) to clean up unused job listings
    from the database.
    
    Similar to Spring Boot's:
        @Scheduled(cron = "0 0 * * *")
        public void cleanupUnusedJobs() { ... }
    """
    try:
        logger.info("Starting scheduled cleanup of unused job listings...")
        call_command('cleanup_unused_jobs')
        logger.info("Scheduled cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled cleanup: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Start the scheduler. This is called when Django starts.
    """
    try:
        # Register events to clean up old job executions
        register_events(scheduler)
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}", exc_info=True)


# Start scheduler when Django is ready
# This prevents issues during migrations and tests
import atexit

# Register shutdown handler
atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

