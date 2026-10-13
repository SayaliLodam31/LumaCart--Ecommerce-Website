from django.contrib import admin
from .models import Cart, CartItem, Coupon, CouponUsage

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price_at_addition', 'subtotal')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items_count', 'subtotal', 'total_amount', 'updated_at')
    search_fields = ('user__email', 'session_key')
    inlines = [CartItemInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_purchase', 'valid_to', 'times_used', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_to')
    search_fields = ('code',)

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'user__email')
