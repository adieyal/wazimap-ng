"""
ViewSets for Dataset and Indicator REST API.

This module provides clean, well-structured viewsets following DRF best practices.
All business logic is in separate service modules - views only handle HTTP concerns.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from wazimap_ng.datasets import models
from wazimap_ng.datasets.api.v1 import serializers
from wazimap_ng.datasets.api.v1 import services
from wazimap_ng.datasets.api.v1.permissions import DatasetPermission, IndicatorPermission


class DatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dataset CRUD operations.

    Provides:
    - list: List all datasets the user has access to
    - retrieve: Get detailed dataset information
    - create: Create a new dataset
    - update: Update an existing dataset
    - partial_update: Partially update a dataset
    - destroy: Delete a dataset
    - upload: Upload data to a dataset (custom action)
    - download_template: Download CSV template (custom action)
    - data: Get dataset data (custom action)
    """

    permission_classes = [IsAuthenticated, DatasetPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['profile', 'permission_type', 'geography_hierarchy']
    search_fields = ['name', 'profile__name']
    ordering_fields = ['name', 'created', 'updated']
    ordering = ['-created']

    def get_queryset(self):
        """
        Return datasets based on user permissions.
        Admin users see all datasets, others see only public datasets
        or those belonging to their profiles.
        """
        user = self.request.user

        if user.is_superuser:
            return models.Dataset.objects.all()

        # Get user's profile groups
        user_groups = user.groups.values_list('name', flat=True)

        # Return public datasets or datasets belonging to user's profiles
        return models.Dataset.objects.filter(
            Q(permission_type='public') |
            Q(profile__name__in=user_groups)
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return serializers.DatasetListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return serializers.DatasetCreateUpdateSerializer
        elif self.action == 'upload':
            return serializers.DatasetFileUploadSerializer
        else:
            return serializers.DatasetDetailSerializer

    def perform_create(self, serializer):
        """Create a new dataset and assign permissions."""
        dataset = serializer.save()
        services.DatasetService.assign_permissions(dataset, self.request.user)

    def perform_destroy(self, instance):
        """Delete dataset and associated data."""
        services.DatasetService.delete_dataset(instance)

    @action(detail=True, methods=['post'])
    def upload(self, request, pk=None):
        """
        Upload data file to a dataset.

        POST /api/v2/datasets/{id}/upload/

        Request body (multipart/form-data):
        - file: CSV/Excel file
        - overwrite: boolean (optional, default: false)
        - update_indicators: boolean (optional, default: false)

        Response:
        - task_id: Celery task ID for tracking upload progress
        - dataset: Updated dataset information
        """
        dataset = self.get_object()
        serializer = serializers.DatasetFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        overwrite = serializer.validated_data.get('overwrite', False)
        update_indicators = serializer.validated_data.get('update_indicators', False)

        # Start upload task
        task_id = services.DatasetService.upload_data(
            dataset=dataset,
            file_obj=file_obj,
            user=request.user,
            overwrite=overwrite,
            update_indicators=update_indicators,
        )

        return Response({
            'task_id': task_id,
            'dataset': serializers.DatasetDetailSerializer(dataset).data,
            'message': 'Upload started successfully. Use the task_id to track progress.'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def download_template(self, request, pk=None):
        """
        Download a CSV template for uploading data to this dataset.

        GET /api/v2/datasets/{id}/download_template/

        Response: CSV file with correct headers
        """
        dataset = self.get_object()
        csv_response = services.DatasetService.generate_template(dataset)
        return csv_response

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Get data rows for this dataset.

        GET /api/v2/datasets/{id}/data/

        Query parameters:
        - geography: Filter by geography code
        - limit: Limit number of results
        - offset: Offset for pagination

        Response: Paginated list of data rows
        """
        dataset = self.get_object()
        geography_code = request.query_params.get('geography')

        queryset = models.DatasetData.objects.filter(dataset=dataset)

        if geography_code:
            queryset = queryset.filter(geography__code=geography_code)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.DatasetDataSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DatasetDataSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def make_public(self, request, pk=None):
        """
        Make a dataset public.

        POST /api/v2/datasets/{id}/make_public/
        """
        dataset = self.get_object()
        dataset.permission_type = 'public'
        dataset.save()

        return Response({
            'message': f'Dataset "{dataset.name}" is now public.',
            'dataset': serializers.DatasetDetailSerializer(dataset).data
        })

    @action(detail=True, methods=['post'])
    def make_private(self, request, pk=None):
        """
        Make a dataset private.

        POST /api/v2/datasets/{id}/make_private/
        """
        dataset = self.get_object()
        dataset.permission_type = 'private'
        dataset.save()

        return Response({
            'message': f'Dataset "{dataset.name}" is now private.',
            'dataset': serializers.DatasetDetailSerializer(dataset).data
        })


class IndicatorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Indicator (Variable) CRUD operations.

    Provides:
    - list: List all indicators the user has access to
    - retrieve: Get detailed indicator information
    - create: Create a new indicator
    - update: Update an existing indicator
    - partial_update: Partially update an indicator
    - destroy: Delete an indicator
    - recalculate: Trigger recalculation of indicator data (custom action)
    - data: Get indicator data (custom action)
    """

    permission_classes = [IsAuthenticated, IndicatorPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dataset', 'universe']
    search_fields = ['name', 'dataset__name']
    ordering_fields = ['name', 'created', 'updated']
    ordering = ['-created']

    def get_queryset(self):
        """
        Return indicators based on user permissions.
        Users only see indicators for datasets they have access to.
        """
        user = self.request.user

        if user.is_superuser:
            return models.Indicator.objects.all()

        # Get user's profile groups
        user_groups = user.groups.values_list('name', flat=True)

        # Return indicators for accessible datasets
        return models.Indicator.objects.filter(
            Q(dataset__permission_type='public') |
            Q(dataset__profile__name__in=user_groups)
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return serializers.IndicatorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return serializers.IndicatorCreateUpdateSerializer
        else:
            return serializers.IndicatorDetailSerializer

    def perform_destroy(self, instance):
        """Delete indicator and associated data."""
        services.IndicatorService.delete_indicator(instance)

    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """
        Trigger recalculation of indicator data.

        POST /api/v2/indicators/{id}/recalculate/

        Response:
        - task_id: Celery task ID for tracking recalculation progress
        - indicator: Indicator information
        """
        indicator = self.get_object()

        task_id = services.IndicatorService.recalculate_data(
            indicator=indicator,
            user=request.user
        )

        return Response({
            'task_id': task_id,
            'indicator': serializers.IndicatorDetailSerializer(indicator).data,
            'message': 'Recalculation started successfully. Use the task_id to track progress.'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Get data rows for this indicator.

        GET /api/v2/indicators/{id}/data/

        Query parameters:
        - geography: Filter by geography code
        - limit: Limit number of results
        - offset: Offset for pagination

        Response: Paginated list of data rows
        """
        indicator = self.get_object()
        geography_code = request.query_params.get('geography')

        queryset = models.IndicatorData.objects.filter(indicator=indicator)

        if geography_code:
            queryset = queryset.filter(geography__code=geography_code)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.IndicatorDataSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.IndicatorDataSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refresh_subindicators(self, request, pk=None):
        """
        Refresh the list of subindicators for this indicator.

        POST /api/v2/indicators/{id}/refresh_subindicators/
        """
        indicator = self.get_object()
        indicator.save(force_subindicator_update=True)

        return Response({
            'message': 'Subindicators refreshed successfully.',
            'indicator': serializers.IndicatorDetailSerializer(indicator).data
        })


class UniverseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Universe CRUD operations.

    Universes are filters that can be applied to indicators.
    """

    queryset = models.Universe.objects.all()
    serializer_class = serializers.UniverseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created', 'updated']
    ordering = ['name']
