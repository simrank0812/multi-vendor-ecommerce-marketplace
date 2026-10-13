from django.db.models import Sum


def cart_count(request):
    if request.user.is_authenticated and request.user.is_customer:
        total = request.user.cart_items.aggregate(n=Sum("quantity"))["n"] or 0
        return {"cart_count": total}
    return {"cart_count": 0}
