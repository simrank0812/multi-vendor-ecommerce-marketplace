from django.contrib import admin

from .models import CartItem, Category, Order, OrderItem, Product, ReturnRequest

admin.site.register(Category)
admin.site.register(CartItem)
admin.site.register(ReturnRequest)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "seller", "category", "price", "stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "total", "created_at")
    inlines = [OrderItemInline]
