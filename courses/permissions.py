# courses/permissions.py
"""
Custom permission classes for the courses API.

Ensures users can only modify their own courses and related objects.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    
    Read permissions are allowed to any authenticated user,
    but write permissions are only allowed to the owner.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            # For courses, check if user is the owner for GET requests too
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsCourseOwner(permissions.BasePermission):
    """
    Permission for nested resources (Module, Lesson).
    
    Ensures the user owns the parent course.
    """
    
    def has_object_permission(self, request, view, obj):
        # Determine the course based on object type
        if hasattr(obj, 'course'):  # Module
            course = obj.course
        elif hasattr(obj, 'module'):  # Lesson
            course = obj.module.course
        else:
            return False
        
        # Check if the requesting user owns the course
        return course.user == request.user
