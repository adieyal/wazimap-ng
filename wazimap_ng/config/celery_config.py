"""
Celery configuration settings.

This module provides Celery configuration that can be mixed into Django settings.
"""
import os
from kombu import Exchange, Queue
from wazimap_ng.utils import int_or_none, truthy


class CeleryConfig:
    """Celery configuration mixin for Django settings."""

    # Broker settings
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = 'django-db'
    CELERY_CACHE_BACKEND = 'default'

    # Task settings
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = int(os.environ.get('CELERY_TASK_TIME_LIMIT', 3600 * 4))  # 4 hours default
    CELERY_TASK_SOFT_TIME_LIMIT = int(os.environ.get('CELERY_TASK_SOFT_TIME_LIMIT', 3600 * 3))  # 3 hours default
    CELERY_TASK_ACKS_LATE = truthy(os.environ.get('CELERY_TASK_ACKS_LATE', True))
    CELERY_TASK_REJECT_ON_WORKER_LOST = True

    # Task result settings
    CELERY_RESULT_EXTENDED = True
    CELERY_RESULT_EXPIRES = int(os.environ.get('CELERY_RESULT_EXPIRES', 86400))  # 24 hours

    # Worker settings
    CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.environ.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1))
    CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.environ.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 100))
    CELERY_WORKER_DISABLE_RATE_LIMITS = False

    # Serialization
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True

    # Task queues
    CELERY_TASK_DEFAULT_QUEUE = 'default'
    CELERY_TASK_DEFAULT_EXCHANGE = 'default'
    CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

    # Define task queues for different priorities
    CELERY_TASK_QUEUES = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('high_priority', Exchange('high_priority'), routing_key='high_priority'),
        Queue('low_priority', Exchange('low_priority'), routing_key='low_priority'),
        Queue('data_processing', Exchange('data_processing'), routing_key='data_processing'),
    )

    # Task routes
    CELERY_TASK_ROUTES = {
        'wazimap_ng.datasets.tasks.*': {'queue': 'data_processing'},
        'wazimap_ng.points.tasks.*': {'queue': 'data_processing'},
    }

    # Beat schedule (periodic tasks) - can be configured as needed
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
    CELERY_BEAT_SCHEDULE = {}

    # Logging
    CELERY_WORKER_HIJACK_ROOT_LOGGER = False
    CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
