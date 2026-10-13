import csv
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    CheckoutValidationSerializer,
    OrderCreateSerializer
)
from apps.cart.models import Cart, CartItem, CouponUsage
from apps.accounts.models import Address
from apps.catalog.models import Inventory, AuditLog
from apps.payments.models import Payment
from apps.payments.razorpay_client import create_razorpay_order, verify_razorpay_signature
from apps.payments.serializers import PaymentVerificationSerializer

class CheckoutValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate stock for all items
        out_of_stock = []
        for item in cart.items.select_related('variant__inventory', 'product'):
            avail = item.variant.inventory.available_stock if hasattr(item.variant, 'inventory') else 0
            if item.quantity > avail:
                out_of_stock.append({
                    'product': item.product.title,
                    'variant': item.variant.sku,
                    'requested': item.quantity,
                    'available': avail
                })

        if out_of_stock:
            return Response({
                'error': 'Some items in your cart exceed available stock.',
                'out_of_stock_items': out_of_stock
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': 'Cart and inventory validated successfully.',
            'subtotal': cart.subtotal,
            'discount': cart.discount_amount,
            'tax': cart.tax_amount,
            'shipping': cart.shipping_charge,
            'total': cart.total_amount
        })

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address_id = serializer.validated_data['address_id']
        shipping_method = serializer.validated_data.get('shipping_method', 'Standard Express (2-4 business days)')
        payment_method = serializer.validated_data.get('payment_method', 'razorpay')
        notes = serializer.validated_data.get('notes', '')

        is_cod = (payment_method.lower() == 'cod') or ('cash on delivery' in shipping_method.lower())

        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response({'error': 'Selected address does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Cannot place order with an empty cart.'}, status=status.HTTP_400_BAD_REQUEST)

        address_snapshot = {
            'full_name': address.full_name,
            'phone_number': address.phone_number,
            'street_address': address.street_address,
            'landmark': address.landmark,
            'city': address.city,
            'state': address.state,
            'postal_code': address.postal_code,
            'country': address.country
        }

        # Safe order creation with row-level locking
        with transaction.atomic():
            cart_items = list(cart.items.select_related('variant', 'product'))

            # Check inventory with row-locking
            for item in cart_items:
                inventory = Inventory.objects.select_for_update().get(variant=item.variant)
                if inventory.available_stock < item.quantity:
                    return Response({
                        'error': f"Insufficient stock for '{item.product.title}' ({item.variant.sku}). Available: {inventory.available_stock}"
                    }, status=status.HTTP_400_BAD_REQUEST)

            order_number = Order.generate_order_number()
            order_status = 'confirmed' if is_cod else 'pending_payment'

            order = Order.objects.create(
                order_number=order_number,
                user=request.user,
                status=order_status,
                subtotal=cart.subtotal,
                discount_amount=cart.discount_amount,
                coupon=cart.coupon,
                tax_amount=cart.tax_amount,
                shipping_fee=cart.shipping_charge,
                total_amount=cart.total_amount,
                shipping_address_json=address_snapshot,
                shipping_method=shipping_method,
                notes=notes
            )

            for item in cart_items:
                variant_name_parts = []
                if item.variant.size:
                    variant_name_parts.append(f"Size: {item.variant.size.name}")
                if item.variant.colour:
                    variant_name_parts.append(f"Color: {item.variant.colour.name}")
                variant_name = ", ".join(variant_name_parts) or "Standard"

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    product_title=item.product.title,
                    variant_name=variant_name,
                    sku=item.variant.sku,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    subtotal=item.subtotal
                )

            if is_cod:
                # Decrement inventory and increment total_sold immediately for confirmed COD order
                for item in cart_items:
                    inv = Inventory.objects.select_for_update().get(variant=item.variant)
                    inv.stock_quantity = max(0, inv.stock_quantity - item.quantity)
                    inv.save(update_fields=['stock_quantity', 'updated_at'])

                    item.product.total_sold += item.quantity
                    item.product.save(update_fields=['total_sold', 'updated_at'])

                # Create COD Payment record (status pending collection on delivery)
                Payment.objects.create(
                    order=order,
                    payment_method='cod',
                    razorpay_order_id=f"COD-{order.order_number}",
                    status='pending',
                    amount=order.total_amount,
                    currency='INR'
                )

                # Record coupon usage
                if order.coupon:
                    CouponUsage.objects.create(coupon=order.coupon, user=request.user)
                    order.coupon.times_used += 1
                    order.coupon.save(update_fields=['times_used'])

                # Clear user's cart
                Cart.objects.filter(user=request.user).delete()

                # Broadcast WebSocket updates
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"user_{request.user.id}",
                        {
                            'type': 'order_status_updated',
                            'order_number': order.order_number,
                            'status': 'confirmed',
                            'message': f"Cash on Delivery order #{order.order_number} placed successfully!"
                        }
                    )
                except Exception:
                    pass

                return Response({
                    'success': True,
                    'cod': True,
                    'message': 'Cash on Delivery order placed successfully.',
                    'order_number': order.order_number,
                    'status': 'confirmed'
                }, status=status.HTTP_201_CREATED)

            # Otherwise, create Razorpay Order for online prepayment
            rzp_order = create_razorpay_order(
                amount_in_rupees=order.total_amount,
                receipt_id=order.order_number,
                notes={'order_number': order.order_number, 'email': request.user.email}
            )

            payment = Payment.objects.create(
                order=order,
                payment_method='razorpay',
                razorpay_order_id=rzp_order['id'],
                status='pending',
                amount=order.total_amount,
                currency='INR'
            )

        return Response({
            'success': True,
            'message': 'Order initiated successfully. Proceed to payment.',
            'order_number': order.order_number,
            'razorpay_order_id': rzp_order['id'],
            'amount_in_paise': rzp_order['amount'],
            'currency': 'INR',
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'user_details': {
                'name': request.user.get_full_name() or request.user.email,
                'email': request.user.email,
                'phone': address.phone_number
            }
        }, status=status.HTTP_201_CREATED)

class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rzp_order_id = serializer.validated_data['razorpay_order_id']
        rzp_payment_id = serializer.validated_data['razorpay_payment_id']
        rzp_signature = serializer.validated_data['razorpay_signature']

        try:
            payment = Payment.objects.select_related('order__user').get(razorpay_order_id=rzp_order_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.order.user != request.user:
            return Response({'error': 'Unauthorized payment verification attempt.'}, status=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate payment verification
        if payment.status == 'successful':
            return Response({
                'success': True,
                'message': 'Payment already verified.',
                'order': OrderSerializer(payment.order).data
            })

        # Server-side cryptographic signature verification
        is_authentic = verify_razorpay_signature(rzp_order_id, rzp_payment_id, rzp_signature)
        if not is_authentic:
            payment.status = 'failed'
            payment.error_code = 'SIGNATURE_VERIFICATION_FAILED'
            payment.error_description = 'Payment signature does not match expected hash.'
            payment.save(update_fields=['status', 'error_code', 'error_description', 'updated_at'])

            payment.order.status = 'payment_failed'
            payment.order.save(update_fields=['status', 'updated_at'])
            return Response({'error': 'Payment verification failed. Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        # Atomically confirm payment, decrement inventory, and clear cart
        with transaction.atomic():
            payment.status = 'successful'
            payment.razorpay_payment_id = rzp_payment_id
            payment.razorpay_signature = rzp_signature
            payment.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])

            order = payment.order
            order.status = 'confirmed'
            order.save(update_fields=['status', 'updated_at'])

            # Decrement inventory and increment total_sold
            for item in order.items.select_related('variant', 'product'):
                inv = Inventory.objects.select_for_update().get(variant=item.variant)
                inv.stock_quantity = max(0, inv.stock_quantity - item.quantity)
                inv.save(update_fields=['stock_quantity', 'updated_at'])

                item.product.total_sold += item.quantity
                item.product.save(update_fields=['total_sold', 'updated_at'])

            # Record coupon usage
            if order.coupon:
                CouponUsage.objects.create(coupon=order.coupon, user=request.user)
                order.coupon.times_used += 1
                order.coupon.save(update_fields=['times_used'])

            # Clear user's cart
            Cart.objects.filter(user=request.user).delete()

            # Broadcast WebSocket updates
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{request.user.id}",
                    {
                        'type': 'order_status_updated',
                        'order_number': order.order_number,
                        'status': 'confirmed',
                        'message': f"Order #{order.order_number} confirmed successfully!"
                    }
                )
            except Exception:
                pass

        return Response({
            'success': True,
            'message': 'Payment successfully verified! Your order is confirmed.',
            'order': OrderSerializer(order).data
        })

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'payment')

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'payment')

class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in ('confirmed', 'pending_payment'):
            return Response({
                'error': f"Cannot cancel order in '{order.get_status_display()}' status. Please contact support."
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # If confirmed, restore inventory
            if order.status == 'confirmed':
                for item in order.items.select_related('variant', 'product'):
                    inv = Inventory.objects.select_for_update().get(variant=item.variant)
                    inv.stock_quantity += item.quantity
                    inv.save(update_fields=['stock_quantity', 'updated_at'])

                    item.product.total_sold = max(0, item.product.total_sold - item.quantity)
                    item.product.save(update_fields=['total_sold', 'updated_at'])

            order.status = 'cancelled'
            order.notes = f"{order.notes or ''}\nCancelled by customer on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            order.save(update_fields=['status', 'notes', 'updated_at'])

        return Response({
            'success': True,
            'message': f"Order #{order.order_number} has been cancelled.",
            'order': OrderSerializer(order).data
        })

class AdminOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related('user', 'payment').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'order_number'

    @action(detail=True, methods=['post'])
    def update_status(self, request, order_number=None):
        order = self.get_object()
        new_status = request.data.get('status')
        tracking_number = request.data.get('tracking_number')

        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Valid status is required.'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        order.save()

        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_ORDER_STATUS',
            model_name='Order',
            object_id=order.order_number,
            changes_json={'old_status': old_status, 'new_status': new_status, 'tracking_number': tracking_number}
        )

        # Notify customer via WebSocket
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{order.user.id}",
                {
                    'type': 'order_status_updated',
                    'order_number': order.order_number,
                    'status': new_status,
                    'message': f"Your order #{order.order_number} status is now {order.get_status_display()}."
                }
            )
        except Exception:
            pass

        return Response({'success': True, 'order': OrderSerializer(order).data})

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        from django.db.models import Sum, Count
        total_revenue = Order.objects.filter(status__in=['confirmed', 'processing', 'shipped', 'delivered']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_orders = Order.objects.count()
        low_stock_count = Inventory.objects.filter(stock_quantity__lte=5).count()
        top_products = OrderItem.objects.values('product_title').annotate(total_qty=Sum('quantity'), revenue=Sum('subtotal')).order_by('-total_qty')[:5]

        return Response({
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'low_stock_count': low_stock_count,
            'top_products': list(top_products)
        })

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="lumacart_orders_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Date', 'Customer Email', 'Status', 'Total (INR)', 'Items Count', 'Shipping City', 'Tracking'])

        for o in Order.objects.all().select_related('user').prefetch_related('items'):
            city = o.shipping_address_json.get('city', '') if isinstance(o.shipping_address_json, dict) else ''
            writer.writerow([
                o.order_number,
                o.created_at.strftime('%Y-%m-%d %H:%M'),
                o.user.email,
                o.get_status_display(),
                o.total_amount,
                o.items.count(),
                city,
                o.tracking_number or 'N/A'
            ])

        return response
