"""
ViewSets for Task Management REST API.

Provides endpoints for monitoring and managing Celery tasks.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from celery.result import AsyncResult
from django_celery_results.models import TaskResult

from wazimap_ng.datasets.api.v1 import serializers
from wazimap_ng.datasets.api.v1 import services


class TaskViewSet(viewsets.ViewSet):
    """
    ViewSet for Task operations.

    Provides:
    - retrieve: Get task status by ID
    - cancel: Cancel a running task
    - list: List recent tasks
    """

    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """
        Get the status of a Celery task.

        GET /api/v2/tasks/{task_id}/

        Response:
        - task_id: Task ID
        - status: Current status (PENDING, STARTED, SUCCESS, FAILURE, REVOKED)
        - result: Task result if completed successfully
        - error: Error message if failed
        """
        task_id = pk
        status_info = services.TaskService.get_task_status(task_id)

        # Try to get additional info from database
        try:
            task_result = TaskResult.objects.get(task_id=task_id)
            status_info['created'] = task_result.date_created
            status_info['started'] = task_result.date_done
            status_info['task_name'] = task_result.task_name
        except TaskResult.DoesNotExist:
            pass

        serializer = serializers.TaskStatusSerializer(status_info)
        return Response(serializer.data)

    def list(self, request):
        """
        List recent tasks.

        GET /api/v2/tasks/

        Query parameters:
        - status: Filter by status
        - limit: Limit number of results (default: 50)

        Response: List of recent tasks
        """
        limit = int(request.query_params.get('limit', 50))
        status_filter = request.query_params.get('status')

        queryset = TaskResult.objects.all().order_by('-date_created')[:limit]

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        tasks = []
        for task_result in queryset:
            task_info = {
                'task_id': task_result.task_id,
                'status': task_result.status,
                'task_name': task_result.task_name,
                'created': task_result.date_created,
                'started': task_result.date_done,
            }

            # Add result or error based on status
            if task_result.status == 'SUCCESS':
                task_info['result'] = task_result.result
            elif task_result.status == 'FAILURE':
                task_info['error'] = task_result.result

            tasks.append(task_info)

        serializer = serializers.TaskStatusSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a running task.

        POST /api/v2/tasks/{task_id}/cancel/

        Response:
        - message: Success message
        """
        task_id = pk

        try:
            services.TaskService.cancel_task(task_id)
            return Response({
                'message': f'Task {task_id} has been cancelled.',
                'task_id': task_id
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
