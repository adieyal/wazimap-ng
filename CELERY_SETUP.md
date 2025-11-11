# Celery Setup Guide for Wazimap-NG

## Overview

Wazimap-NG has been migrated from Django-Q to Celery for background task processing. This guide explains how to set up and run Celery workers.

## What is Celery?

Celery is a distributed task queue system that allows you to run background tasks asynchronously. It's more robust and scalable than Django-Q, with better monitoring, error handling, and task management capabilities.

## Installation

The required packages are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs:
- `celery==5.2.7` - Core Celery library
- `django-celery-beat==2.4.0` - Periodic task scheduling
- `django-celery-results==2.4.0` - Task result storage in Django database

## Configuration

### Settings

Celery configuration is in `wazimap_ng/config/celery_config.py` and is automatically included in Django settings.

Key configuration:
- **Broker**: Redis (same as Django-Q)
- **Result Backend**: Django database
- **Task Queues**:
  - `default` - General tasks
  - `high_priority` - High priority tasks
  - `low_priority` - Low priority tasks
  - `data_processing` - Dataset and indicator processing

### Environment Variables

```bash
# Redis URL (required)
REDIS_URL=redis://localhost:6379/0

# Optional Celery settings
CELERY_TASK_TIME_LIMIT=14400           # 4 hours default
CELERY_TASK_SOFT_TIME_LIMIT=10800      # 3 hours default
CELERY_WORKER_PREFETCH_MULTIPLIER=1    # Number of tasks to prefetch
CELERY_WORKER_MAX_TASKS_PER_CHILD=100  # Restart worker after N tasks
```

## Running Celery

### Run Migrations

First, run migrations to create the necessary database tables for task results:

```bash
python manage.py migrate django_celery_results
python manage.py migrate django_celery_beat
```

### Start Celery Worker

**Development:**

```bash
celery -A wazimap_ng worker --loglevel=info
```

**Production:**

```bash
celery -A wazimap_ng worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --time-limit=14400
```

### Start Celery Beat (for periodic tasks)

If you need to run periodic tasks:

```bash
celery -A wazimap_ng beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Run Worker and Beat Together

For development:

```bash
celery -A wazimap_ng worker --beat --loglevel=info
```

### Multiple Queues

To process different queues with different workers:

```bash
# Worker for data processing (heavy tasks)
celery -A wazimap_ng worker --loglevel=info --queues=data_processing --concurrency=2

# Worker for general tasks
celery -A wazimap_ng worker --loglevel=info --queues=default,high_priority,low_priority --concurrency=4
```

## Monitoring

### Celery Flower

Flower is a web-based monitoring tool for Celery:

```bash
# Install Flower
pip install flower

# Run Flower
celery -A wazimap_ng flower --port=5555
```

Then visit http://localhost:5555 to see:
- Real-time task monitoring
- Worker status
- Task history
- Task statistics

### Command-line Monitoring

```bash
# See active tasks
celery -A wazimap_ng inspect active

# See registered tasks
celery -A wazimap_ng inspect registered

# See worker stats
celery -A wazimap_ng inspect stats

# See reserved tasks
celery -A wazimap_ng inspect reserved
```

## Task Types

### Dataset Upload Processing

**Task**: `wazimap_ng.datasets.tasks.process_dataset_upload`

Processes uploaded CSV/Excel files and loads data into the database.

- **Queue**: `data_processing`
- **Time Limit**: 4 hours
- **Retry**: Automatic on failure

### Indicator Data Extraction

**Task**: `wazimap_ng.datasets.tasks.extract_indicator_data`

Extracts and aggregates indicator data from dataset data.

- **Queue**: `data_processing`
- **Time Limit**: 2 hours
- **Retry**: Automatic on failure

### Dataset Deletion

**Task**: `wazimap_ng.datasets.tasks.delete_dataset_data`

Deletes a dataset and all associated data.

- **Queue**: `data_processing`
- **Time Limit**: 1 hour

### Indicator Deletion

**Task**: `wazimap_ng.datasets.tasks.delete_indicator_data`

Deletes an indicator and all associated data.

- **Queue**: `data_processing`
- **Time Limit**: 30 minutes

## Production Deployment

### Using systemd

Create a systemd service file `/etc/systemd/system/celery-wazimap.service`:

```ini
[Unit]
Description=Celery Worker for Wazimap-NG
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/wazimap-ng
Environment=DJANGO_SETTINGS_MODULE=wazimap_ng.config
Environment=DJANGO_CONFIGURATION=Production

ExecStart=/path/to/venv/bin/celery -A wazimap_ng worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --pidfile=/var/run/celery-wazimap.pid \
  --logfile=/var/log/celery-wazimap.log

ExecStop=/path/to/venv/bin/celery -A wazimap_ng control shutdown
PIDFile=/var/run/celery-wazimap.pid

Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-wazimap
sudo systemctl start celery-wazimap
sudo systemctl status celery-wazimap
```

### Using Supervisor

Create a supervisor config file `/etc/supervisor/conf.d/celery-wazimap.conf`:

```ini
[program:celery-wazimap-worker]
command=/path/to/venv/bin/celery -A wazimap_ng worker --loglevel=info --concurrency=4
directory=/path/to/wazimap-ng
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-wazimap-worker.log

[program:celery-wazimap-beat]
command=/path/to/venv/bin/celery -A wazimap_ng beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/wazimap-ng
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-wazimap-beat.log
```

Update and restart supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery-wazimap-worker celery-wazimap-beat
```

### Using Docker

If running in Docker, add to your `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A wazimap_ng worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - db
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=...
    volumes:
      - ./:/app

  celery_beat:
    build: .
    command: celery -A wazimap_ng beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - redis
      - db
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=...
```

## Migration from Django-Q

### Differences

| Feature | Django-Q | Celery |
|---------|----------|--------|
| Broker | Redis/ORM | Redis |
| Result Backend | ORM | Django ORM (configurable) |
| Task definition | Function with decorator | Function with decorator |
| Periodic tasks | Schedule model | django-celery-beat |
| Monitoring | Admin panel | Flower + CLI |
| Task chains | Limited | Full support |
| Task groups | Limited | Full support |

### Code Changes

**Old (Django-Q):**
```python
from django_q.tasks import async_task

task_id = async_task(
    "wazimap_ng.datasets.tasks.process_uploaded_file",
    dataset_file, dataset,
    hook="wazimap_ng.datasets.hooks.process_task_info"
)
```

**New (Celery):**
```python
from wazimap_ng.datasets.tasks.celery_tasks import process_dataset_upload

task = process_dataset_upload.apply_async(
    args=[dataset_file.id, dataset.id]
)
task_id = task.id
```

### Running Both Systems in Parallel

During migration, you can run both Django-Q and Celery in parallel:

1. Keep Django-Q running for existing tasks
2. Start Celery workers for new tasks
3. Gradually migrate code to use Celery
4. Once all tasks are migrated, stop Django-Q

## Troubleshooting

### Worker not starting

**Error**: "kombu.exceptions.OperationalError"

**Solution**: Ensure Redis is running:
```bash
redis-cli ping
# Should respond with "PONG"
```

### Tasks not executing

**Check**:
1. Is the worker running?
2. Is the task registered? `celery -A wazimap_ng inspect registered`
3. Are there any errors in worker logs?
4. Is the queue correct?

### Task timeout

**Increase time limits** in `celery_config.py`:
```python
CELERY_TASK_TIME_LIMIT = 21600  # 6 hours
CELERY_TASK_SOFT_TIME_LIMIT = 18000  # 5 hours
```

### Memory issues

**Reduce concurrency**:
```bash
celery -A wazimap_ng worker --concurrency=2
```

**Restart workers after N tasks**:
```bash
celery -A wazimap_ng worker --max-tasks-per-child=50
```

### View task logs

Check the Celery worker output or:
```bash
tail -f /var/log/celery-wazimap.log
```

## Best Practices

1. **Use task IDs**: Always store and return task IDs so users can track progress
2. **Set time limits**: All tasks should have reasonable time limits
3. **Handle errors**: Use try/except in tasks and log errors
4. **Update progress**: Use `self.update_state()` to report progress
5. **Use queues**: Separate heavy tasks from light tasks using different queues
6. **Monitor**: Use Flower to monitor task execution in production
7. **Test tasks**: Test tasks thoroughly before deploying
8. **Retry logic**: Use Celery's automatic retry for transient failures

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django-Celery-Results](https://django-celery-results.readthedocs.io/)
- [Django-Celery-Beat](https://django-celery-beat.readthedocs.io/)
- [Flower Documentation](https://flower.readthedocs.io/)
