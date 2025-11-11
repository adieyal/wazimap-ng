"""
Serializers for Dataset and Indicator REST API.

This module provides clean, well-structured serializers for all dataset-related operations.
No dynamic attribute access (getattr) - everything is explicit and clear.
"""
from rest_framework import serializers
from wazimap_ng.datasets import models
from wazimap_ng.profile.models import Profile


class GeographyHierarchySerializer(serializers.ModelSerializer):
    """Serializer for geography hierarchy information."""

    root_geography_code = serializers.CharField(
        source='root_geography.code',
        read_only=True
    )
    root_geography_name = serializers.CharField(
        source='root_geography.name',
        read_only=True
    )

    class Meta:
        model = models.GeographyHierarchy
        fields = [
            'id',
            'name',
            'description',
            'root_geography_code',
            'root_geography_name',
        ]
        read_only_fields = ['id']


class DatasetListSerializer(serializers.ModelSerializer):
    """Serializer for listing datasets (minimal fields)."""

    profile_name = serializers.CharField(
        source='profile.name',
        read_only=True
    )
    geography_hierarchy_name = serializers.CharField(
        source='geography_hierarchy.name',
        read_only=True
    )
    indicator_count = serializers.SerializerMethodField()
    data_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Dataset
        fields = [
            'id',
            'name',
            'profile',
            'profile_name',
            'geography_hierarchy',
            'geography_hierarchy_name',
            'groups',
            'permission_type',
            'indicator_count',
            'data_count',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']

    def get_indicator_count(self, obj):
        """Get the number of indicators for this dataset."""
        return obj.indicator_set.count()

    def get_data_count(self, obj):
        """Get the number of data rows for this dataset."""
        return models.DatasetData.objects.filter(dataset=obj).count()


class DatasetDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed dataset information."""

    profile_name = serializers.CharField(
        source='profile.name',
        read_only=True
    )
    geography_hierarchy_detail = GeographyHierarchySerializer(
        source='geography_hierarchy',
        read_only=True
    )
    indicators = serializers.SerializerMethodField()

    class Meta:
        model = models.Dataset
        fields = [
            'id',
            'name',
            'profile',
            'profile_name',
            'geography_hierarchy',
            'geography_hierarchy_detail',
            'groups',
            'permission_type',
            'indicators',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']

    def get_indicators(self, obj):
        """Get all indicators for this dataset."""
        indicators = obj.indicator_set.all()
        return IndicatorListSerializer(indicators, many=True).data


class DatasetCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating datasets."""

    class Meta:
        model = models.Dataset
        fields = [
            'id',
            'name',
            'profile',
            'geography_hierarchy',
            'permission_type',
        ]
        read_only_fields = ['id', 'groups']

    def validate_profile(self, value):
        """Ensure the user has permission to create/update datasets for this profile."""
        request = self.context.get('request')
        if request and request.user:
            if not request.user.groups.filter(name=value.name).exists():
                raise serializers.ValidationError(
                    "You do not have permission to create/update datasets for this profile."
                )
        return value

    def validate_name(self, value):
        """Ensure the dataset name is not empty and has valid length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Dataset name cannot be empty.")
        if len(value) > 60:
            raise serializers.ValidationError("Dataset name cannot exceed 60 characters.")
        return value.strip()


class IndicatorListSerializer(serializers.ModelSerializer):
    """Serializer for listing indicators (minimal fields)."""

    dataset_name = serializers.CharField(
        source='dataset.name',
        read_only=True
    )
    universe_name = serializers.CharField(
        source='universe.name',
        read_only=True,
        allow_null=True
    )
    subindicator_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Indicator
        fields = [
            'id',
            'name',
            'dataset',
            'dataset_name',
            'universe',
            'universe_name',
            'groups',
            'subindicator_count',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']

    def get_subindicator_count(self, obj):
        """Get the number of subindicators."""
        if obj.subindicators:
            return len(obj.subindicators)
        return 0


class IndicatorDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed indicator information."""

    dataset_name = serializers.CharField(
        source='dataset.name',
        read_only=True
    )
    dataset_profile = serializers.CharField(
        source='dataset.profile.name',
        read_only=True
    )
    universe_detail = serializers.SerializerMethodField()
    data_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Indicator
        fields = [
            'id',
            'name',
            'dataset',
            'dataset_name',
            'dataset_profile',
            'universe',
            'universe_detail',
            'groups',
            'subindicators',
            'data_count',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']

    def get_universe_detail(self, obj):
        """Get universe detail if it exists."""
        if obj.universe:
            return UniverseSerializer(obj.universe).data
        return None

    def get_data_count(self, obj):
        """Get the number of data rows for this indicator."""
        return models.IndicatorData.objects.filter(indicator=obj).count()


class IndicatorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating indicators."""

    class Meta:
        model = models.Indicator
        fields = [
            'id',
            'name',
            'dataset',
            'universe',
            'groups',
        ]
        read_only_fields = ['id', 'subindicators']

    def validate_dataset(self, value):
        """Ensure the user has permission to create/update indicators for this dataset."""
        request = self.context.get('request')
        if request and request.user and value.profile:
            if not request.user.groups.filter(name=value.profile.name).exists():
                raise serializers.ValidationError(
                    "You do not have permission to create/update indicators for this dataset."
                )
        return value

    def validate_name(self, value):
        """Ensure the indicator name is not empty and has valid length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Indicator name cannot be empty.")
        if len(value) > 50:
            raise serializers.ValidationError("Indicator name cannot exceed 50 characters.")
        return value.strip()

    def validate_groups(self, value):
        """Ensure groups are valid for the dataset."""
        if value:
            dataset = self.initial_data.get('dataset')
            if dataset:
                dataset_obj = models.Dataset.objects.filter(id=dataset).first()
                if dataset_obj and dataset_obj.groups:
                    invalid_groups = [g for g in value if g not in dataset_obj.groups]
                    if invalid_groups:
                        raise serializers.ValidationError(
                            f"Invalid groups: {invalid_groups}. "
                            f"Must be one of: {dataset_obj.groups}"
                        )
        return value


class UniverseSerializer(serializers.ModelSerializer):
    """Serializer for universe filters."""

    class Meta:
        model = models.Universe
        fields = [
            'id',
            'name',
            'filters',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']


class DatasetDataSerializer(serializers.ModelSerializer):
    """Serializer for dataset data rows."""

    geography_code = serializers.CharField(
        source='geography.code',
        read_only=True
    )
    geography_name = serializers.CharField(
        source='geography.name',
        read_only=True
    )

    class Meta:
        model = models.DatasetData
        fields = [
            'id',
            'dataset',
            'geography',
            'geography_code',
            'geography_name',
            'data',
        ]
        read_only_fields = ['id']


class IndicatorDataSerializer(serializers.ModelSerializer):
    """Serializer for indicator data rows."""

    geography_code = serializers.CharField(
        source='geography.code',
        read_only=True
    )
    geography_name = serializers.CharField(
        source='geography.name',
        read_only=True
    )
    indicator_name = serializers.CharField(
        source='indicator.name',
        read_only=True
    )

    class Meta:
        model = models.IndicatorData
        fields = [
            'id',
            'indicator',
            'indicator_name',
            'geography',
            'geography_code',
            'geography_name',
            'data',
        ]
        read_only_fields = ['id']


class DatasetFileUploadSerializer(serializers.Serializer):
    """Serializer for dataset file uploads."""

    file = serializers.FileField(required=True)
    overwrite = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether to overwrite existing data"
    )
    update_indicators = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether to update related indicators after upload"
    )

    def validate_file(self, value):
        """Validate the uploaded file."""
        from django.conf import settings

        # Check file size
        if value.size > settings.FILE_SIZE_LIMIT:
            raise serializers.ValidationError(
                f"File size exceeds the maximum limit of "
                f"{settings.FILE_SIZE_LIMIT / (1024 * 1024)} MB"
            )

        # Check file extension
        extension = value.name.split('.')[-1].lower()
        if extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '{extension}' is not allowed. "
                f"Allowed types: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )

        return value


class TaskStatusSerializer(serializers.Serializer):
    """Serializer for task status responses."""

    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    progress = serializers.IntegerField(required=False, allow_null=True)
    created = serializers.DateTimeField(required=False, allow_null=True)
    started = serializers.DateTimeField(required=False, allow_null=True)
    completed = serializers.DateTimeField(required=False, allow_null=True)
