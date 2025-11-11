"""
Celery configuration for Wazimap-NG.

This module sets up Celery for handling background tasks such as:
- Dataset file processing
- Indicator data extraction
- Point data uploads
- Data deletion operations
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wazimap_ng.config')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Local')

# Import django-configurations
import configurations
configurations.setup()

# Create the Celery app
app = Celery('wazimap_ng')

# Load configuration from Django settings with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
