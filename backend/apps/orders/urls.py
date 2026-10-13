from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CheckoutValidateView,
    OrderCreateView,
    PaymentVerifyView,
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    AdminOrderViewSet
)

router = DefaultRouter()
router.register(r'admin/orders', AdminOrderViewSet, basename='admin-order')

urlpatterns = [
    path('checkout/validate/', CheckoutValidateView.as_view(), name='checkout_validate'),
    path('orders/create/', OrderCreateView.as_view(), name='order_create'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<str:order_number>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<str:order_number>/cancel/', OrderCancelView.as_view(), name='order_cancel'),
    path('', include(router.urls)),
]
