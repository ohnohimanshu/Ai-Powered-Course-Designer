# ai_engine/urls.py
"""
URL configuration for the ai_engine API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LLMPromptLogViewSet

router = DefaultRouter()
router.register(r'llm-logs', LLMPromptLogViewSet, basename='llmpromptlog')

urlpatterns = [
    path('', include(router.urls)),
]
