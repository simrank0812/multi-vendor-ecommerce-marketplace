"""Seller dashboard: analytics, products, orders, returns."""
from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required

from .forms import ProductForm
from .models import OrderItem, Product, ReturnRequest
from .views import restore_stock

seller_only = role_required("seller")
approved_seller = role_required("seller", approved_seller=True)


@seller_only
def dashboard(request):
    profile = request.user.seller_profile
    context = {"profile": profile}
    if profile.is_approved:
        items = OrderItem.objects.filter(seller=request.user).exclude(status__in=OrderItem.INACTIVE)
        gross = sum((i.line_total for i in items), Decimal("0"))
        commission = sum((i.commission_amount for i in items), Decimal("0"))

        # last 7 days sales for the bar chart
        today = timezone.localdate()
        days = OrderedDict((today - timedelta(days=n), Decimal("0")) for n in range(6, -1, -1))
        for i in items.select_related("order"):
            d = timezone.localtime(i.order.created_at).date()
            if d in days:
                days[d] += i.line_total
        chart = [{"label": d.strftime("%a"), "value": float(v)} for d, v in days.items()]

        top = {}
        for i in items:
            top[i.product_name] = top.get(i.product_name, 0) + i.quantity
        top = sorted(top.items(), key=lambda x: -x[1])[:5]

        context.update({
            "gross": gross, "commission": commission, "net": gross - commission,
            "orders_count": items.values("order").distinct().count(),
            "units": sum(i.quantity for i in items),
            "products_count": request.user.products.count(),
            "low_stock": request.user.products.filter(stock__lte=5).order_by("stock")[:5],
            "pending_orders": OrderItem.objects.filter(seller=request.user, status__in=["placed", "processing"]).count(),
            "pending_returns": ReturnRequest.objects.filter(item__seller=request.user, status="requested").count(),
            "chart": chart, "top": top,
        })
    return render(request, "seller/dashboard.html", context)


@approved_seller
def product_list(request):
    return render(request, "seller/products.html", {"products": request.user.products.select_related("category")})


@approved_seller
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        messages.success(request, "Product added.")
        return redirect("seller_products")
    return render(request, "seller/product_form.html", {"form": form, "title": "Add product"})


@approved_seller
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("seller_products")
    return render(request, "seller/product_form.html", {"form": form, "title": "Edit product"})


@approved_seller
@require_POST
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk, seller=request.user).delete()
    messages.success(request, "Product deleted.")
    return redirect("seller_products")


@approved_seller
@require_POST
def stock_update(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    try:
        product.stock = max(int(request.POST.get("stock", product.stock)), 0)
        product.save(update_fields=["stock"])
        messages.success(request, f"Stock for '{product.name}' set to {product.stock}.")
    except ValueError:
        messages.error(request, "Invalid stock value.")
    return redirect("seller_products")


@approved_seller
def orders(request):
    status = request.GET.get("status", "")
    items = OrderItem.objects.filter(seller=request.user).select_related("order__customer").order_by("-order__created_at")
    if status:
        items = items.filter(status=status)
    return render(request, "seller/orders.html", {"items": items, "status": status, "statuses": OrderItem.STATUS_CHOICES})


@approved_seller
@require_POST
def advance_order(request, pk):
    item = get_object_or_404(OrderItem, pk=pk, seller=request.user)
    if item.next_status:
        item.status = item.next_status
        item.save()
        messages.success(request, f"Order item #{item.pk} marked {item.status}.")
    return redirect(request.META.get("HTTP_REFERER") or "seller_orders")


@approved_seller
def returns(request):
    reqs = ReturnRequest.objects.filter(item__seller=request.user).select_related("item__order__customer")
    return render(request, "seller/returns.html", {"requests": reqs})


@approved_seller
@require_POST
def decide_return(request, pk):
    rr = get_object_or_404(ReturnRequest, pk=pk, item__seller=request.user, status=ReturnRequest.REQUESTED)
    if request.POST.get("decision") == "approve":
        rr.status = ReturnRequest.APPROVED
        rr.item.status = OrderItem.RETURNED
        rr.item.save()
        restore_stock(rr.item)
        messages.success(request, "Return approved. Stock restored and commission reversed.")
    else:
        rr.status = ReturnRequest.REJECTED
        messages.info(request, "Return rejected.")
    rr.save()
    return redirect("seller_returns")
