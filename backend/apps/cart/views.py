from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction

from .models import Cart, CartItem, Coupon
from .serializers import CartSerializer, CartItemSerializer
from apps.catalog.models import Product, ProductVariant

def get_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    
    session_key = request.headers.get('X-Session-Key') or request.session.session_key
    if not session_key:
        if not request.session.exists(request.session.session_key):
            request.session.create()
        session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_cart_for_request(request)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

class CartItemAddView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = get_cart_for_request(request)
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))

        if not variant_id or quantity <= 0:
            return Response({'error': 'Valid variant_id and positive quantity are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            variant = ProductVariant.objects.select_related('product', 'inventory').get(id=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Selected product variant was not found.'}, status=status.HTTP_404_NOT_FOUND)

        available_stock = variant.inventory.available_stock if hasattr(variant, 'inventory') else 0

        # Check existing item in cart
        cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()
        current_in_cart = cart_item.quantity if cart_item else 0
        total_requested = current_in_cart + quantity

        if total_requested > available_stock:
            return Response({
                'error': f"Only {available_stock} units available in stock. You currently have {current_in_cart} in cart."
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if cart_item:
                cart_item.quantity = total_requested
                cart_item.save(update_fields=['quantity', 'updated_at'])
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=variant.product,
                    variant=variant,
                    quantity=quantity,
                    price_at_addition=variant.effective_price
                )

        serializer = CartSerializer(cart, context={'request': request})
        return Response({
            'success': True,
            'message': f"Added '{variant.product.title}' to cart.",
            'cart': serializer.data
        }, status=status.HTTP_201_CREATED)

class CartItemDetailView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, pk):
        cart = get_cart_for_request(request)
        try:
            item = CartItem.objects.select_related('variant__inventory').get(id=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', 0))
        if quantity <= 0:
            item.delete()
            serializer = CartSerializer(cart, context={'request': request})
            return Response({'success': True, 'message': 'Item removed from cart.', 'cart': serializer.data})

        available_stock = item.variant.inventory.available_stock if hasattr(item.variant, 'inventory') else 0
        if quantity > available_stock:
            return Response({
                'error': f"Cannot update quantity. Only {available_stock} items remaining in stock."
            }, status=status.HTTP_400_BAD_REQUEST)

        item.quantity = quantity
        item.save(update_fields=['quantity', 'updated_at'])

        serializer = CartSerializer(cart, context={'request': request})
        return Response({'success': True, 'message': 'Cart updated.', 'cart': serializer.data})

    def delete(self, request, pk):
        cart = get_cart_for_request(request)
        try:
            item = CartItem.objects.get(id=pk, cart=cart)
            item.delete()
            serializer = CartSerializer(cart, context={'request': request})
            return Response({'success': True, 'message': 'Item removed from cart.', 'cart': serializer.data})
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

class ClearCartView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_cart_for_request(request)
        cart.items.all().delete()
        cart.coupon = None
        cart.save(update_fields=['coupon', 'updated_at'])
        serializer = CartSerializer(cart, context={'request': request})
        return Response({'success': True, 'message': 'Cart cleared.', 'cart': serializer.data})

class MergeCartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'User must be authenticated to merge cart.'}, status=status.HTTP_401_UNAUTHORIZED)

        guest_session_key = request.data.get('session_key') or request.headers.get('X-Session-Key')
        if not guest_session_key:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart, context={'request': request})
            return Response({'success': True, 'cart': serializer.data})

        with transaction.atomic():
            user_cart, _ = Cart.objects.get_or_create(user=request.user)
            guest_cart = Cart.objects.filter(session_key=guest_session_key).first()

            if guest_cart:
                for guest_item in guest_cart.items.all():
                    existing_user_item = user_cart.items.filter(variant=guest_item.variant).first()
                    avail_stock = guest_item.variant.inventory.available_stock if hasattr(guest_item.variant, 'inventory') else 0

                    if existing_user_item:
                        new_qty = min(avail_stock, existing_user_item.quantity + guest_item.quantity)
                        existing_user_item.quantity = max(1, new_qty)
                        existing_user_item.save(update_fields=['quantity', 'updated_at'])
                    else:
                        CartItem.objects.create(
                            cart=user_cart,
                            product=guest_item.product,
                            variant=guest_item.variant,
                            quantity=min(avail_stock, guest_item.quantity),
                            price_at_addition=guest_item.price_at_addition
                        )
                # Clean up guest cart
                guest_cart.items.all().delete()
                guest_cart.delete()

        serializer = CartSerializer(user_cart, context={'request': request})
        return Response({'success': True, 'message': 'Guest cart merged successfully.', 'cart': serializer.data})

class ApplyCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        if not code:
            return Response({'error': 'Coupon code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        cart = get_cart_for_request(request)
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_404_NOT_FOUND)

        is_valid, msg = coupon.is_valid(cart.subtotal)
        if not is_valid:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        cart.coupon = coupon
        cart.save(update_fields=['coupon', 'updated_at'])

        serializer = CartSerializer(cart, context={'request': request})
        return Response({
            'success': True,
            'message': f"Coupon '{coupon.code}' applied successfully!",
            'cart': serializer.data
        })

class RemoveCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = get_cart_for_request(request)
        cart.coupon = None
        cart.save(update_fields=['coupon', 'updated_at'])
        serializer = CartSerializer(cart, context={'request': request})
        return Response({'success': True, 'message': 'Coupon removed.', 'cart': serializer.data})
