from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = 'Job Search'
    
    def ready(self):
        """Start scheduled tasks when Django is ready"""
        # Only start scheduler in production/development, not during migrations or tests
        import sys
        if 'migrate' not in sys.argv and 'test' not in sys.argv:
            try:
                from jobs.scheduled_tasks import start_scheduler
                start_scheduler()
            except Exception as e:
                logger.warning(f"Could not start scheduler: {e}")