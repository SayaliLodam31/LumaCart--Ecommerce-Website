from rest_framework import serializers
from .models import Payment

class PaymentVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(required=True)
    razorpay_payment_id = serializers.CharField(required=True)
    razorpay_signature = serializers.CharField(required=True)

class PaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'order', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'status', 'amount', 'currency', 'created_at')
