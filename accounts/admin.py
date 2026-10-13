from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SellerProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Marketplace", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role",)


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("store_name", "user", "status", "commission_rate")
    list_filter = ("status",)
