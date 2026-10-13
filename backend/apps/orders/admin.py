from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'product_title', 'variant_name', 'sku', 'unit_price', 'quantity', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'shipping_method', 'tracking_number', 'created_at')
    list_filter = ('status', 'created_at', 'shipping_method')
    search_fields = ('order_number', 'user__email', 'tracking_number')
    readonly_fields = ('order_number', 'user', 'subtotal', 'discount_amount', 'tax_amount', 'shipping_fee', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
