# evaluation/urls.py
"""
URL configuration for the evaluation API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluationResultViewSet, ConceptMasteryViewSet

router = DefaultRouter()
router.register(r'evaluations', EvaluationResultViewSet, basename='evaluationresult')
router.register(r'concept-mastery', ConceptMasteryViewSet, basename='conceptmastery')

urlpatterns = [
    path('', include(router.urls)),
]
