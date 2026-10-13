from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'status', 'amount', 'currency', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'order__order_number', 'order__user__email')
    readonly_fields = ('order', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'amount', 'currency', 'created_at', 'updated_at')
