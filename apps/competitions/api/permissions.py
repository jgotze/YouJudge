from rest_framework import permissions


class IsCompetitionOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a competition to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the competition.
        return obj.created_by == request.user


class IsJudgeOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow judges or competition owner to access.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is the competition owner
        if hasattr(obj, 'created_by'):
            if obj.created_by == request.user:
                return True

        # Allow if user is an accepted judge
        if hasattr(obj, 'competition'):
            return obj.competition.can_user_judge(request.user)

        return False
