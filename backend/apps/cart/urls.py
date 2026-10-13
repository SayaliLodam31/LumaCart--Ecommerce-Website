from django.urls import path
from .views import (
    CartView,
    CartItemAddView,
    CartItemDetailView,
    ClearCartView,
    MergeCartView,
    ApplyCouponView,
    RemoveCouponView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart_detail'),
    path('cart/items/', CartItemAddView.as_view(), name='cart_item_add'),
    path('cart/items/<int:pk>/', CartItemDetailView.as_view(), name='cart_item_detail'),
    path('cart/clear/', ClearCartView.as_view(), name='cart_clear'),
    path('cart/merge/', MergeCartView.as_view(), name='cart_merge'),
    path('cart/apply-coupon/', ApplyCouponView.as_view(), name='cart_apply_coupon'),
    path('cart/remove-coupon/', RemoveCouponView.as_view(), name='cart_remove_coupon'),
]
