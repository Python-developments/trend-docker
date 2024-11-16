from rest_framework.permissions import BasePermission


class IsBlockerSelf(BasePermission):
    """
    Ensure that users can only create blocks for themselves
    """
    def has_permission(self, request, view):
        blocker_username = request.query_params.get('blocker')
        user = request.user

        if blocker_username:
            # Check if the requesting user is the same as the blocker user
            if user.username == blocker_username:
                return True  # Allow access
            else:
                return False  # Deny access
        return True  # Allow if no blocker filter is applied