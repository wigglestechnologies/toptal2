from rest_framework.permissions import BasePermission


class IsPlayerOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        else:
            return obj.team.owner == request.user

class IsTeamOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        else:
            return obj.owner == request.user