from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_permission_required(permission):
    """
    Require authentication and a specific Django permission
    assigned through the user's custom Role.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if not request.user.has_perm(permission):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator