"""
Permissions for Dataset and Indicator REST API.

This module provides clean, explicit permission classes.
No dynamic attribute access - everything is clear and straightforward.
"""
from rest_framework import permissions


class DatasetPermission(permissions.BasePermission):
    """
    Permission class for Dataset operations.

    Rules:
    - Superusers can do anything
    - Authenticated users can view public datasets
    - Users can view/edit datasets for their assigned profiles
    - Users can only create datasets for profiles they're assigned to
    """

    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can do anything
        if request.user.is_superuser:
            return True

        # Read-only access is allowed for all authenticated users
        # (object-level permissions will filter what they can see)
        if request.method in permissions.SAFE_METHODS:
            return True

        # For create/update/delete, user must be in a profile group
        user_groups = request.user.groups.values_list('name', flat=True)
        if not user_groups:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access this specific dataset."""
        # Superusers can do anything
        if request.user.is_superuser:
            return True

        # Anyone can view public datasets
        if request.method in permissions.SAFE_METHODS:
            if obj.permission_type == 'public':
                return True

        # Users can access datasets for their assigned profiles
        if obj.profile:
            if request.user.groups.filter(name=obj.profile.name).exists():
                return True

        return False


class IndicatorPermission(permissions.BasePermission):
    """
    Permission class for Indicator operations.

    Rules:
    - Superusers can do anything
    - Authenticated users can view indicators for public datasets
    - Users can view/edit indicators for datasets in their assigned profiles
    - Users can only create indicators for datasets in their assigned profiles
    """

    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can do anything
        if request.user.is_superuser:
            return True

        # Read-only access is allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # For create/update/delete, user must be in a profile group
        user_groups = request.user.groups.values_list('name', flat=True)
        if not user_groups:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access this specific indicator."""
        # Superusers can do anything
        if request.user.is_superuser:
            return True

        # Anyone can view indicators for public datasets
        if request.method in permissions.SAFE_METHODS:
            if obj.dataset.permission_type == 'public':
                return True

        # Users can access indicators for datasets in their assigned profiles
        if obj.dataset.profile:
            if request.user.groups.filter(name=obj.dataset.profile.name).exists():
                return True

        return False
