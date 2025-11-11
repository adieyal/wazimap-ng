"""
URL routing for Dataset and Indicator REST API v1.

Clean, RESTful URL structure using Django REST Framework routers.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from wazimap_ng.datasets.api.v1 import views, task_views

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'datasets', views.DatasetViewSet, basename='dataset')
router.register(r'indicators', views.IndicatorViewSet, basename='indicator')
router.register(r'universes', views.UniverseViewSet, basename='universe')
router.register(r'tasks', task_views.TaskViewSet, basename='task')

app_name = 'datasets_api_v1'

urlpatterns = [
    path('', include(router.urls)),
]
