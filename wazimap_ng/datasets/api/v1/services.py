"""
Service layer for Dataset and Indicator operations.

This module contains all business logic for datasets and indicators.
Views should only handle HTTP concerns and delegate to these services.
No dynamic attribute access - everything is explicit and clean.
"""
import csv
import logging
from io import StringIO
from django.http import HttpResponse
from django.db import transaction
from guardian.shortcuts import assign_perm

from wazimap_ng.datasets import models
from wazimap_ng.datasets.tasks.celery_tasks import (
    process_dataset_upload,
    extract_indicator_data,
    delete_dataset_data
)

logger = logging.getLogger(__name__)


class DatasetService:
    """Service class for Dataset operations."""

    @staticmethod
    def assign_permissions(dataset, user):
        """
        Assign permissions for a dataset to the appropriate group.

        Args:
            dataset: Dataset instance
            user: User who created the dataset
        """
        if dataset.profile:
            from wazimap_ng.general.services.permissions import assign_perms_to_group
            assign_perms_to_group(dataset.profile.name, dataset, is_private=False)
            logger.info(f"Assigned permissions for dataset {dataset.id} to group {dataset.profile.name}")

    @staticmethod
    def upload_data(dataset, file_obj, user, overwrite=False, update_indicators=False):
        """
        Upload data file to a dataset.

        Args:
            dataset: Dataset instance
            file_obj: Uploaded file object
            user: User performing the upload
            overwrite: Whether to overwrite existing data
            update_indicators: Whether to update related indicators

        Returns:
            str: Celery task ID
        """
        # Create DatasetFile record
        dataset_file = models.DatasetFile.objects.create(
            name=dataset.name,
            document=file_obj,
            dataset=dataset
        )

        # Start Celery task for processing
        task = process_dataset_upload.apply_async(
            args=[dataset_file.id, dataset.id],
            kwargs={
                'overwrite': overwrite,
                'update_indicators': update_indicators,
                'user_id': user.id
            }
        )

        # Store task ID in DatasetFile for tracking
        dataset_file.task_id = task.id
        dataset_file.save(update_fields=['task_id'])

        logger.info(
            f"Started upload task {task.id} for dataset {dataset.id} by user {user.id}"
        )

        return task.id

    @staticmethod
    def delete_dataset(dataset):
        """
        Delete a dataset and all associated data.

        This is done asynchronously for large datasets.

        Args:
            dataset: Dataset instance
        """
        dataset_id = dataset.id
        dataset_name = dataset.name

        # Start async deletion task
        task = delete_dataset_data.apply_async(args=[dataset_id])

        logger.info(
            f"Started deletion task {task.id} for dataset {dataset_id} ({dataset_name})"
        )

        # Note: The actual deletion happens in the Celery task
        # to avoid timeout for large datasets

    @staticmethod
    def generate_template(dataset):
        """
        Generate a CSV template for uploading data to a dataset.

        Args:
            dataset: Dataset instance

        Returns:
            HttpResponse with CSV file
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{dataset.name}_template.csv"'

        writer = csv.writer(response)

        # Write header row
        headers = ['geography_code']
        if dataset.groups:
            headers.extend(dataset.groups)
        headers.append('count')

        writer.writerow(headers)

        # Write one example row
        example_row = ['EXAMPLE_CODE']
        if dataset.groups:
            example_row.extend(['Example Value'] * len(dataset.groups))
        example_row.append('100')

        writer.writerow(example_row)

        logger.info(f"Generated CSV template for dataset {dataset.id}")

        return response

    @staticmethod
    def get_dataset_statistics(dataset):
        """
        Get statistics for a dataset.

        Args:
            dataset: Dataset instance

        Returns:
            dict: Statistics including row count, geography count, etc.
        """
        stats = {
            'total_rows': models.DatasetData.objects.filter(dataset=dataset).count(),
            'indicator_count': dataset.indicator_set.count(),
            'geography_count': models.DatasetData.objects.filter(
                dataset=dataset
            ).values('geography').distinct().count(),
        }

        return stats


class IndicatorService:
    """Service class for Indicator operations."""

    @staticmethod
    def recalculate_data(indicator, user):
        """
        Trigger recalculation of indicator data.

        Args:
            indicator: Indicator instance
            user: User triggering the recalculation

        Returns:
            str: Celery task ID
        """
        # Start Celery task for extraction
        task = extract_indicator_data.apply_async(
            args=[indicator.id],
            kwargs={'user_id': user.id}
        )

        logger.info(
            f"Started recalculation task {task.id} for indicator {indicator.id} by user {user.id}"
        )

        return task.id

    @staticmethod
    def delete_indicator(indicator):
        """
        Delete an indicator and all associated data.

        Args:
            indicator: Indicator instance
        """
        indicator_id = indicator.id
        indicator_name = indicator.name

        # Delete indicator data
        data_count = models.IndicatorData.objects.filter(indicator=indicator).count()
        models.IndicatorData.objects.filter(indicator=indicator).delete()

        # Delete the indicator itself
        indicator.delete()

        logger.info(
            f"Deleted indicator {indicator_id} ({indicator_name}) and {data_count} data rows"
        )

    @staticmethod
    def get_indicator_statistics(indicator):
        """
        Get statistics for an indicator.

        Args:
            indicator: Indicator instance

        Returns:
            dict: Statistics including row count, geography count, etc.
        """
        stats = {
            'total_rows': models.IndicatorData.objects.filter(indicator=indicator).count(),
            'geography_count': models.IndicatorData.objects.filter(
                indicator=indicator
            ).values('geography').distinct().count(),
            'subindicator_count': len(indicator.subindicators) if indicator.subindicators else 0,
        }

        return stats


class TaskService:
    """Service class for Celery task operations."""

    @staticmethod
    def get_task_status(task_id):
        """
        Get the status of a Celery task.

        Args:
            task_id: Celery task ID

        Returns:
            dict: Task status information
        """
        from celery.result import AsyncResult

        task_result = AsyncResult(task_id)

        status_info = {
            'task_id': task_id,
            'status': task_result.status,
            'result': None,
            'error': None,
        }

        if task_result.successful():
            status_info['result'] = task_result.result
        elif task_result.failed():
            status_info['error'] = str(task_result.info)

        return status_info

    @staticmethod
    def cancel_task(task_id):
        """
        Cancel a running Celery task.

        Args:
            task_id: Celery task ID

        Returns:
            bool: True if task was cancelled
        """
        from celery.result import AsyncResult

        task_result = AsyncResult(task_id)
        task_result.revoke(terminate=True)

        logger.info(f"Cancelled task {task_id}")

        return True

    @staticmethod
    def retry_task(task_id):
        """
        Retry a failed task.

        Args:
            task_id: Celery task ID

        Returns:
            str: New task ID
        """
        # This would need to be implemented based on specific task types
        # For now, just log that it was requested
        logger.warning(f"Retry requested for task {task_id} but not yet implemented")
        raise NotImplementedError("Task retry is not yet implemented")
