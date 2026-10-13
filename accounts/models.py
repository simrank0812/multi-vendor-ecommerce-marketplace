from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN, SELLER, CUSTOMER = "admin", "seller", "customer"
    ROLE_CHOICES = [(ADMIN, "Admin"), (SELLER, "Seller"), (CUSTOMER, "Customer")]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER)
    phone = models.CharField(max_length=15, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

    @property
    def is_seller(self):
        return self.role == self.SELLER

    @property
    def is_customer(self):
        return self.role == self.CUSTOMER


class SellerProfile(models.Model):
    PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
    STATUS_CHOICES = [(PENDING, "Pending"), (APPROVED, "Approved"), (REJECTED, "Rejected")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    store_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("10.00"),
                                          help_text="Percent of each sale kept by the marketplace")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name

    @property
    def is_approved(self):
        return self.status == self.APPROVED
