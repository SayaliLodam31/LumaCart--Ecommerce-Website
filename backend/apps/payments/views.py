from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Payment
from .serializers import PaymentDetailSerializer

class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'razorpay_order_id'

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)
