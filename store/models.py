from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    image_url = models.URLField(blank=True)
    icon = models.CharField(max_length=4, blank=True, default="🛒")

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Optional: link to a product photo (used if no file is uploaded)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.pk])

    @property
    def picture(self):
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def low_stock(self):
        return 0 < self.stock <= 5


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("user", "product")

    @property
    def line_total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    PAYMENT_CHOICES = [("cod", "Cash on Delivery"), ("upi", "UPI (demo)"), ("card", "Card (demo)")]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="cod")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    PLACED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, RETURNED = (
        "placed", "processing", "shipped", "delivered", "cancelled", "returned")
    STATUS_CHOICES = [(PLACED, "Placed"), (PROCESSING, "Processing"), (SHIPPED, "Shipped"),
                      (DELIVERED, "Delivered"), (CANCELLED, "Cancelled"), (RETURNED, "Returned")]
    FLOW = [PLACED, PROCESSING, SHIPPED, DELIVERED]
    NEXT = {PLACED: PROCESSING, PROCESSING: SHIPPED, SHIPPED: DELIVERED}
    # statuses that do not count towards sales / commission
    INACTIVE = (CANCELLED, RETURNED)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sold_items")
    product_name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PLACED)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity

    @property
    def seller_earning(self):
        return self.line_total - self.commission_amount

    @property
    def next_status(self):
        return self.NEXT.get(self.status)

    @property
    def step_index(self):
        return self.FLOW.index(self.status) if self.status in self.FLOW else -1

    @property
    def can_cancel(self):
        return self.status == self.PLACED

    @property
    def can_return(self):
        return self.status == self.DELIVERED and not hasattr(self, "return_request")


class ReturnRequest(models.Model):
    REQUESTED, APPROVED, REJECTED = "requested", "approved", "rejected"
    STATUS_CHOICES = [(REQUESTED, "Requested"), (APPROVED, "Approved"), (REJECTED, "Rejected")]

    item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="return_request")
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
