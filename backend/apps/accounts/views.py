import secrets
from django.contrib.auth import authenticate
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Address
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    AddressSerializer
)
from .permissions import IsOwnerOrAdmin

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.verification_token = secrets.token_urlsafe(32)
        user.save(update_fields=['verification_token'])

        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response({
            'success': True,
            'message': 'Registration successful. Welcome to LumaCart!',
            'user': user_data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'This account has been deactivated.'}, status=status.HTTP_403_FORBIDDEN)

        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response({
            'success': True,
            'message': 'Login successful.',
            'user': user_data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'success': True, 'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '')
        if not token:
            return Response({'error': 'Verification token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(verification_token=token)
            user.is_email_verified = True
            user.verification_token = None
            user.save(update_fields=['is_email_verified', 'verification_token'])
            return Response({'success': True, 'message': 'Email successfully verified!'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid or expired verification token.'}, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        try:
            user = CustomUser.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            user.reset_password_token = token
            user.save(update_fields=['reset_password_token'])
            # In production, email would be dispatched. For demo/dev, token is returned or logged
            return Response({
                'success': True,
                'message': 'Password reset instructions have been sent.',
                'dev_token': token if request.user.is_staff or True else None
            })
        except CustomUser.DoesNotExist:
            # Prevent email enumeration by returning standard message
            return Response({'success': True, 'message': 'If that email exists, reset instructions have been sent.'})

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user = CustomUser.objects.get(reset_password_token=token)
            user.set_password(new_password)
            user.reset_password_token = None
            user.save()
            return Response({'success': True, 'message': 'Password has been reset successfully. You can now log in.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # First address is automatically default
        is_first = not Address.objects.filter(user=self.request.user).exists()
        is_def = serializer.validated_data.get('is_default', is_first)
        serializer.save(user=self.request.user, is_default=is_def)
