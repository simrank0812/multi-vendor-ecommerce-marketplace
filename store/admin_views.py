"""Marketplace admin panel (separate from the built-in Django admin)."""
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import SellerProfile, User

from .forms import CommissionForm
from .models import Order, OrderItem, Product

admin_only = role_required("admin")


@admin_only
def dashboard(request):
    active = OrderItem.objects.exclude(status__in=OrderItem.INACTIVE)
    gmv = sum((i.line_total for i in active), Decimal("0"))
    commission = sum((i.commission_amount for i in active), Decimal("0"))
    return render(request, "admin_panel/dashboard.html", {
        "gmv": gmv, "commission": commission,
        "sellers": SellerProfile.objects.count(),
        "pending": SellerProfile.objects.filter(status="pending").select_related("user"),
        "customers": User.objects.filter(role="customer").count(),
        "products": Product.objects.count(),
        "orders": Order.objects.count(),
        "recent_orders": Order.objects.select_related("customer")[:6],
    })


@admin_only
def sellers(request):
    return render(request, "admin_panel/sellers.html", {"profiles": SellerProfile.objects.select_related("user")})


@admin_only
@require_POST
def seller_decision(request, pk):
    profile = get_object_or_404(SellerProfile, pk=pk)
    decision = request.POST.get("decision")
    if decision in ("approved", "rejected", "pending"):
        profile.status = decision
        profile.save()
        messages.success(request, f"{profile.store_name} is now {decision}.")
    return redirect(request.META.get("HTTP_REFERER") or "admin_sellers")


@admin_only
@require_POST
def seller_commission(request, pk):
    profile = get_object_or_404(SellerProfile, pk=pk)
    form = CommissionForm(request.POST)
    if form.is_valid():
        profile.commission_rate = form.cleaned_data["commission_rate"]
        profile.save()
        messages.success(request, f"Commission for {profile.store_name} set to {profile.commission_rate}% (applies to new orders).")
    else:
        messages.error(request, "Enter a commission between 0 and 100.")
    return redirect("admin_sellers")


@admin_only
def products(request):
    return render(request, "admin_panel/products.html", {"products": Product.objects.select_related("seller__seller_profile", "category")})


@admin_only
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    messages.success(request, f"'{product.name}' is now {'visible' if product.is_active else 'hidden'}.")
    return redirect("admin_products")


@admin_only
def orders(request):
    return render(request, "admin_panel/orders.html", {"orders": Order.objects.select_related("customer").prefetch_related("items")})


@admin_only
def commissions(request):
    rows = {}
    for i in OrderItem.objects.exclude(status__in=OrderItem.INACTIVE).select_related("seller__seller_profile"):
        r = rows.setdefault(i.seller_id, {"store": i.seller.seller_profile.store_name, "sales": Decimal("0"), "commission": Decimal("0")})
        r["sales"] += i.line_total
        r["commission"] += i.commission_amount
    return render(request, "admin_panel/commissions.html", {"rows": sorted(rows.values(), key=lambda r: -r["commission"])})
