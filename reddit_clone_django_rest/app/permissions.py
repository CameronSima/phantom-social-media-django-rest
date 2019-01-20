from rest_framework import permissions
from pprint import pprint


class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.author == request.user

class IsAdminOrReadOnly(permissions.BasePermission):

    # To edit a sub, a user must be authenticated and either 
    # be an admin or only subscribing or unsubscribing.
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_authenticated():
            if view.action == 'subscribe' or view.action == 'unsubscribe':
                return True
            
            if request.user.id in obj.admins.all():
                return True
                
        return False

