from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    BrandViewSet,
    SizeViewSet,
    ColourViewSet,
    ProductViewSet,
    HomeBannerViewSet,
    AdminCatalogViewSet,
    WishlistView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'sizes', SizeViewSet, basename='size')
router.register(r'colours', ColourViewSet, basename='colour')
router.register(r'banners', HomeBannerViewSet, basename='banner')
router.register(r'admin/products', AdminCatalogViewSet, basename='admin-product')

urlpatterns = [
    path('wishlist/', WishlistView.as_view(), name='wishlist_detail'),
    path('wishlist/<int:pk>/', WishlistView.as_view(), name='wishlist_delete'),
    path('', include(router.urls)),
]

