from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    VerifyEmailView,
    ForgotPasswordView,
    ResetPasswordView,
    AddressViewSet
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', LoginView.as_view(), name='auth_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth_forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth_reset_password'),
    path('', include(router.urls)),
]
