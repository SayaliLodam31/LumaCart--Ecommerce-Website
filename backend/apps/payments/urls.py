from django.urls import path
from .views import PaymentDetailView

urlpatterns = [
    path('payments/<str:razorpay_order_id>/', PaymentDetailView.as_view(), name='payment_detail'),
]
