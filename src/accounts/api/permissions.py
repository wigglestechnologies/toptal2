from rest_framework.permissions import BasePermission

class IsAdminOrSelf(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        else:
            return obj == request.user
