from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        if user.is_seller:
            messages.info(request, "Registration received. An admin must verify your store before you can sell.")
        else:
            messages.success(request, "Welcome! Your account has been created.")
        return redirect("dashboard_redirect")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard_redirect(request):
    if request.user.is_admin_role:
        return redirect("admin_dashboard")
    if request.user.is_seller:
        return redirect("seller_dashboard")
    return redirect("home")
