"""Customer-facing views: browsing, cart, checkout, orders, returns."""
import json
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import SellerProfile

from .forms import CheckoutForm, ReturnForm
from .models import CartItem, Category, Order, OrderItem, Product, ReturnRequest

customer_only = role_required("customer")


def visible_products():
    return Product.objects.filter(is_active=True, seller__seller_profile__status="approved") \
        .select_related("category", "seller__seller_profile")


def product_list(request):
    products = visible_products()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    sort = request.GET.get("sort", "new")
    seller = request.GET.get("seller", "")

    if q:
        products = products.filter(name__icontains=q) | products.filter(description__icontains=q)
    if category:
        products = products.filter(category__slug=category)
    if seller:
        products = products.filter(seller_id=seller)
    try:
        if min_price:
            products = products.filter(price__gte=Decimal(min_price))
        if max_price:
            products = products.filter(price__lte=Decimal(max_price))
    except Exception:
        messages.error(request, "Please enter valid prices.")
    products = products.order_by({"low": "price", "high": "-price", "new": "-created_at"}.get(sort, "-created_at"))

    page = Paginator(products.distinct(), 8).get_page(request.GET.get("page"))
    filtered = any([q, category, min_price, max_price, seller]) or sort != "new" or page.number > 1
    stores = SellerProfile.objects.filter(status="approved").select_related("user")
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "product_list.html", {
        "page": page, "categories": Category.objects.all(), "show_hero": not filtered, "stores": stores, "querystring": params.urlencode(),
        "f": {"q": q, "category": category, "min_price": min_price, "max_price": max_price, "sort": sort},
    })


def product_detail(request, pk):
    product = get_object_or_404(visible_products(), pk=pk)
    related = visible_products().filter(category=product.category).exclude(pk=pk)[:4]
    return render(request, "product_detail.html", {"product": product, "related": related})


# ---------------- cart ----------------
@customer_only
def cart_view(request):
    items = request.user.cart_items.select_related("product")
    total = sum(i.line_total for i in items)
    return render(request, "cart.html", {"items": items, "total": total})


@require_POST
def cart_add(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "message": "Please log in to add items.", "login": True}, status=401)
    if not request.user.is_customer:
        return JsonResponse({"ok": False, "message": "Only customer accounts can shop."}, status=403)
    data = json.loads(request.body or "{}")
    product = get_object_or_404(visible_products(), pk=data.get("product_id"))
    qty = max(int(data.get("quantity", 1)), 1)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={"quantity": 0})
    new_qty = item.quantity + qty
    if new_qty > product.stock:
        if created:
            item.delete()
        return JsonResponse({"ok": False, "message": f"Only {product.stock} in stock."}, status=400)
    item.quantity = new_qty
    item.save()
    count = request.user.cart_items.aggregate(n=Sum("quantity"))["n"] or 0
    return JsonResponse({"ok": True, "message": f"Added '{product.name}' to cart", "count": count})


@customer_only
@require_POST
def cart_update(request):
    data = json.loads(request.body or "{}")
    item = get_object_or_404(CartItem, pk=data.get("item_id"), user=request.user)
    qty = int(data.get("quantity", 1))
    if qty <= 0:
        item.delete()
    elif qty > item.product.stock:
        return JsonResponse({"ok": False, "message": f"Only {item.product.stock} in stock."}, status=400)
    else:
        item.quantity = qty
        item.save()
    items = request.user.cart_items.select_related("product")
    total = sum(i.line_total for i in items)
    count = sum(i.quantity for i in items)
    return JsonResponse({
        "ok": True, "total": f"{total:.2f}", "count": count,
        "line_total": f"{item.line_total:.2f}" if qty > 0 else "0.00", "removed": qty <= 0,
    })


# ---------------- checkout ----------------
@customer_only
def checkout(request):
    items = list(request.user.cart_items.select_related("product__seller__seller_profile"))
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("home")
    total = sum(i.line_total for i in items)
    form = CheckoutForm(request.POST or None, initial={
        "full_name": request.user.get_full_name() or request.user.username, "phone": request.user.phone})

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                order = form.save(commit=False)
                order.customer = request.user
                order.total = total
                order.save()
                for ci in items:
                    product = Product.objects.select_for_update().get(pk=ci.product_id)
                    if not product.is_active or ci.quantity > product.stock:
                        raise ValueError(f"'{product.name}' does not have enough stock.")
                    rate = product.seller.seller_profile.commission_rate
                    line = product.price * ci.quantity
                    OrderItem.objects.create(
                        order=order, product=product, seller=product.seller, product_name=product.name,
                        price=product.price, quantity=ci.quantity, commission_rate=rate,
                        commission_amount=(line * rate / 100).quantize(Decimal("0.01")))
                    product.stock -= ci.quantity
                    product.save(update_fields=["stock"])
                request.user.cart_items.all().delete()
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("cart")
        messages.success(request, f"Order #{order.pk} placed successfully!")
        return redirect("order_detail", pk=order.pk)
    return render(request, "checkout.html", {"form": form, "items": items, "total": total})


# ---------------- orders / returns ----------------
@customer_only
def my_orders(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "orders.html", {"orders": orders})


@customer_only
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items__seller__seller_profile"), pk=pk, customer=request.user)
    return render(request, "order_detail.html", {"order": order, "steps": OrderItem.FLOW, "return_form": ReturnForm()})


def restore_stock(item):
    if item.product_id:
        Product.objects.filter(pk=item.product_id).update(stock=item.product.stock + item.quantity)


@customer_only
@require_POST
def cancel_item(request, pk):
    item = get_object_or_404(OrderItem, pk=pk, order__customer=request.user)
    if item.can_cancel:
        item.status = OrderItem.CANCELLED
        item.save()
        restore_stock(item)
        messages.success(request, f"'{item.product_name}' was cancelled.")
    else:
        messages.error(request, "This item can no longer be cancelled.")
    return redirect("order_detail", pk=item.order_id)


@customer_only
@require_POST
def request_return(request, pk):
    item = get_object_or_404(OrderItem, pk=pk, order__customer=request.user)
    form = ReturnForm(request.POST)
    if item.can_return and form.is_valid():
        ReturnRequest.objects.create(item=item, reason=form.cleaned_data["reason"])
        messages.success(request, "Return request sent to the seller.")
    else:
        messages.error(request, "Return could not be requested for this item.")
    return redirect("order_detail", pk=item.order_id)
