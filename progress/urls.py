# progress/urls.py
"""
URL configuration for the progress API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonProgressViewSet, CourseProgressViewSet

router = DefaultRouter()
router.register(r'lesson-progress', LessonProgressViewSet, basename='lessonprogress')
router.register(r'course-progress', CourseProgressViewSet, basename='courseprogress')

urlpatterns = [
    path('', include(router.urls)),
]
