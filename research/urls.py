# research/urls.py
"""
URL configuration for the research API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResourceViewSet, ResourceChunkViewSet, EmbeddingIndexViewSet

router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'resource-chunks', ResourceChunkViewSet, basename='resourcechunk')
router.register(r'embedding-indexes', EmbeddingIndexViewSet, basename='embeddingindex')

urlpatterns = [
    path('', include(router.urls)),
]
