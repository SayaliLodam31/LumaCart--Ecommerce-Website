import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.catalog.models import Product, ProductVariant
from apps.cart.models import Coupon

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('payment_failed', 'Payment Failed'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    )

    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders', db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_payment', db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address_json = models.JSONField(default=dict)
    shipping_method = models.CharField(max_length=100, default='Standard Express (2-4 business days)')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def generate_order_number(cls):
        date_str = timezone.now().strftime('%Y%m%d')
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"LMC-{date_str}-{unique_suffix}"

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    product_title = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.product_title} in Order #{self.order.order_number}"
