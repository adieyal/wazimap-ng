"""
Celery tasks for dataset and indicator operations.

This module contains Celery tasks that replace Django-Q tasks.
All tasks are clean, well-structured, and follow Celery best practices.
No dynamic attribute access - everything is explicit.
"""
import logging
from celery import shared_task
from django.db import transaction
from django.core.mail import mail_admins
from django.contrib.auth import get_user_model

from wazimap_ng.datasets import models
from wazimap_ng.datasets.tasks.process_uploaded_file import process_uploaded_file as process_file_logic
from wazimap_ng.datasets.tasks.indicator_data_extraction import indicator_data_extraction as extract_indicator_logic

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    name='wazimap_ng.datasets.tasks.process_dataset_upload',
    time_limit=14400,  # 4 hours
    soft_time_limit=10800,  # 3 hours
    acks_late=True,
    reject_on_worker_lost=True
)
def process_dataset_upload(self, dataset_file_id, dataset_id, overwrite=False, update_indicators=False, user_id=None):
    """
    Process uploaded dataset file.

    This task:
    1. Reads the uploaded CSV/Excel file in chunks
    2. Validates and loads data into DatasetData model
    3. Updates dataset groups
    4. Optionally triggers indicator recalculation
    5. Logs errors and warnings to separate files

    Args:
        dataset_file_id: ID of the DatasetFile instance
        dataset_id: ID of the Dataset instance
        overwrite: Whether to overwrite existing data
        update_indicators: Whether to trigger indicator recalculation
        user_id: ID of the user who initiated the upload

    Returns:
        dict: Result information including errors and warnings
    """
    task_id = self.request.id
    logger.info(f"Starting dataset upload task {task_id} for dataset {dataset_id}")

    try:
        # Get the dataset file and dataset
        dataset_file = models.DatasetFile.objects.get(id=dataset_file_id)
        dataset = models.Dataset.objects.get(id=dataset_id)

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting upload'})

        # Process the file using existing logic
        result = process_file_logic(
            dataset_file=dataset_file,
            dataset=dataset,
            overwrite=overwrite
        )

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 80, 'status': 'Upload complete, processing indicators'})

        # If requested, trigger indicator recalculation for all indicators in this dataset
        if update_indicators:
            indicators = models.Indicator.objects.filter(dataset=dataset)
            for indicator in indicators:
                extract_indicator_data.apply_async(
                    args=[indicator.id],
                    kwargs={'user_id': user_id}
                )
            result['indicators_updated'] = indicators.count()

        # Mark as complete
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Complete'})

        logger.info(f"Completed dataset upload task {task_id} for dataset {dataset_id}")

        # Send success notification if user exists
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                logger.info(f"Dataset upload completed for user {user.username}")
            except User.DoesNotExist:
                pass

        return result

    except models.DatasetFile.DoesNotExist:
        error_msg = f"DatasetFile {dataset_file_id} not found"
        logger.error(error_msg)
        raise

    except models.Dataset.DoesNotExist:
        error_msg = f"Dataset {dataset_id} not found"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Error processing dataset upload: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Send email notification on failure
        try:
            mail_admins(
                subject=f'Dataset Upload Failed: {dataset_id}',
                message=f'Task ID: {task_id}\nDataset ID: {dataset_id}\nError: {str(e)}'
            )
        except Exception as email_error:
            logger.error(f"Failed to send error email: {email_error}")

        raise


@shared_task(
    bind=True,
    name='wazimap_ng.datasets.tasks.extract_indicator_data',
    time_limit=7200,  # 2 hours
    soft_time_limit=5400,  # 1.5 hours
    acks_late=True,
    reject_on_worker_lost=True
)
def extract_indicator_data(self, indicator_id, user_id=None):
    """
    Extract and aggregate indicator data from dataset data.

    This task:
    1. Deletes existing indicator data
    2. Aggregates data from DatasetData grouped by geography
    3. Applies universe filters if specified
    4. Bulk creates new IndicatorData rows

    Args:
        indicator_id: ID of the Indicator instance
        user_id: ID of the user who initiated the extraction

    Returns:
        dict: Result information including number of rows created
    """
    task_id = self.request.id
    logger.info(f"Starting indicator data extraction task {task_id} for indicator {indicator_id}")

    try:
        # Get the indicator
        indicator = models.Indicator.objects.get(id=indicator_id)

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting extraction'})

        # Build universe filter kwargs if universe exists
        universe_filters = None
        if indicator.universe:
            universe_filters = indicator.universe.filters

        # Process using existing logic
        result_objs = extract_indicator_logic(
            indicator=indicator,
            universe=universe_filters
        )

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Complete'})

        result = {
            'indicator_id': indicator_id,
            'rows_created': len(result_objs),
            'indicator_name': indicator.name
        }

        logger.info(
            f"Completed indicator data extraction task {task_id} for indicator {indicator_id}. "
            f"Created {len(result_objs)} rows."
        )

        return result

    except models.Indicator.DoesNotExist:
        error_msg = f"Indicator {indicator_id} not found"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Error extracting indicator data: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Send email notification on failure
        try:
            mail_admins(
                subject=f'Indicator Extraction Failed: {indicator_id}',
                message=f'Task ID: {task_id}\nIndicator ID: {indicator_id}\nError: {str(e)}'
            )
        except Exception as email_error:
            logger.error(f"Failed to send error email: {email_error}")

        raise


@shared_task(
    bind=True,
    name='wazimap_ng.datasets.tasks.delete_dataset_data',
    time_limit=3600,  # 1 hour
    soft_time_limit=2700,  # 45 minutes
    acks_late=True,
    reject_on_worker_lost=True
)
def delete_dataset_data(self, dataset_id):
    """
    Delete a dataset and all associated data.

    This task:
    1. Deletes all IndicatorData for indicators in this dataset
    2. Deletes all Indicators for this dataset
    3. Deletes all DatasetData for this dataset
    4. Deletes the Dataset itself

    Args:
        dataset_id: ID of the Dataset instance

    Returns:
        dict: Result information including counts of deleted objects
    """
    task_id = self.request.id
    logger.info(f"Starting dataset deletion task {task_id} for dataset {dataset_id}")

    try:
        # Get the dataset
        dataset = models.Dataset.objects.get(id=dataset_id)
        dataset_name = dataset.name

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Deleting indicator data'})

        # Delete indicator data first
        indicator_data_count = models.IndicatorData.objects.filter(
            indicator__dataset=dataset
        ).count()
        models.IndicatorData.objects.filter(indicator__dataset=dataset).delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 33, 'status': 'Deleting indicators'})

        # Delete indicators
        indicator_count = dataset.indicator_set.count()
        dataset.indicator_set.all().delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 66, 'status': 'Deleting dataset data'})

        # Delete dataset data
        dataset_data_count = models.DatasetData.objects.filter(dataset=dataset).count()
        models.DatasetData.objects.filter(dataset=dataset).delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Deleting dataset'})

        # Delete the dataset itself
        dataset.delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Complete'})

        result = {
            'dataset_id': dataset_id,
            'dataset_name': dataset_name,
            'indicator_data_deleted': indicator_data_count,
            'indicators_deleted': indicator_count,
            'dataset_data_deleted': dataset_data_count
        }

        logger.info(
            f"Completed dataset deletion task {task_id} for dataset {dataset_id}. "
            f"Deleted {indicator_count} indicators, {indicator_data_count} indicator data rows, "
            f"and {dataset_data_count} dataset data rows."
        )

        return result

    except models.Dataset.DoesNotExist:
        error_msg = f"Dataset {dataset_id} not found"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Error deleting dataset: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@shared_task(
    bind=True,
    name='wazimap_ng.datasets.tasks.delete_indicator_data',
    time_limit=1800,  # 30 minutes
    soft_time_limit=1200,  # 20 minutes
    acks_late=True,
    reject_on_worker_lost=True
)
def delete_indicator_data(self, indicator_id):
    """
    Delete an indicator and all associated data.

    This task:
    1. Deletes all IndicatorData for this indicator
    2. Deletes the Indicator itself

    Args:
        indicator_id: ID of the Indicator instance

    Returns:
        dict: Result information including count of deleted objects
    """
    task_id = self.request.id
    logger.info(f"Starting indicator deletion task {task_id} for indicator {indicator_id}")

    try:
        # Get the indicator
        indicator = models.Indicator.objects.get(id=indicator_id)
        indicator_name = indicator.name

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Deleting indicator data'})

        # Delete indicator data
        indicator_data_count = models.IndicatorData.objects.filter(indicator=indicator).count()
        models.IndicatorData.objects.filter(indicator=indicator).delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Deleting indicator'})

        # Delete the indicator itself
        indicator.delete()

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Complete'})

        result = {
            'indicator_id': indicator_id,
            'indicator_name': indicator_name,
            'indicator_data_deleted': indicator_data_count
        }

        logger.info(
            f"Completed indicator deletion task {task_id} for indicator {indicator_id}. "
            f"Deleted {indicator_data_count} indicator data rows."
        )

        return result

    except models.Indicator.DoesNotExist:
        error_msg = f"Indicator {indicator_id} not found"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Error deleting indicator: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise
