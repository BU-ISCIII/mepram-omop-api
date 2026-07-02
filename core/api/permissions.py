from rest_framework.permissions import BasePermission


class IsRootUserForPost(BasePermission):
    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        user = getattr(request, "user", None)
        return bool(
            user
            and getattr(user, "is_authenticated", False)
            and getattr(user, "is_superuser", False)
        )