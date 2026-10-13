from rest_framework import serializers
from .models import Order, OrderItem
from apps.payments.models import Payment

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'variant', 'product_title', 'variant_name', 'sku', 'unit_price', 'quantity', 'subtotal')

class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'status', 'amount', 'currency', 'created_at')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = OrderPaymentSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'status_display', 'subtotal',
            'discount_amount', 'tax_amount', 'shipping_fee', 'total_amount',
            'shipping_address_json', 'shipping_method', 'tracking_number',
            'notes', 'items', 'payment', 'created_at', 'created_at_formatted'
        )

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d %B %Y, %I:%M %p')

class CheckoutValidationSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
    shipping_method = serializers.CharField(required=False, default='Standard Express (2-4 business days)')
    notes = serializers.CharField(required=False, allow_blank=True)

class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
    shipping_method = serializers.CharField(required=False, default='Standard Express (2-4 business days)')
    payment_method = serializers.CharField(required=False, default='razorpay')
    notes = serializers.CharField(required=False, allow_blank=True)
