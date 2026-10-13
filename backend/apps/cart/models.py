from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.catalog.models import Product, ProductVariant

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
    )

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total maximum uses allowed")
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    def is_valid(self, subtotal=Decimal('0.00')):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is no longer active."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired."
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "Coupon usage limit reached."
        if subtotal < self.min_purchase:
            return False, f"Minimum purchase of ₹{self.min_purchase} required for this coupon."
        return True, "Coupon is valid."

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
            if self.max_discount and discount > self.max_discount:
                discount = self.max_discount
        else:
            discount = self.discount_value
        return min(discount, subtotal)

    def __str__(self):
        return self.code

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def discount_amount(self):
        if self.coupon:
            valid, _ = self.coupon.is_valid(self.subtotal)
            if valid:
                return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def shipping_charge(self):
        # Free shipping on orders over ₹3000, else flat ₹150
        if self.subtotal >= Decimal('3000.00') or self.subtotal == Decimal('0.00'):
            return Decimal('0.00')
        return Decimal('150.00')

    @property
    def tax_amount(self):
        # 12% GST on discounted subtotal
        taxable = max(Decimal('0.00'), self.subtotal - self.discount_amount)
        return round((taxable * Decimal('0.12')), 2)

    @property
    def total_amount(self):
        taxable = max(Decimal('0.00'), self.subtotal - self.discount_amount)
        return taxable + self.tax_amount + self.shipping_charge

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_key})"
        return f"Cart of {owner}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'variant')
        ordering = ['-created_at']

    @property
    def unit_price(self):
        return self.variant.effective_price

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.variant.sku} in Cart"

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"
