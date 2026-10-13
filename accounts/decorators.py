from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles, approved_seller=False):
    """Restrict a view to given roles. Sellers may additionally need admin approval."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to open that page.")
                return redirect("home")
            if approved_seller and request.user.is_seller:
                profile = getattr(request.user, "seller_profile", None)
                if not profile or not profile.is_approved:
                    messages.warning(request, "Your seller account is not approved yet.")
                    return redirect("seller_dashboard")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
