import hmac
import hashlib
from decimal import Decimal
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, Address
from apps.catalog.models import Category, Product, ProductVariant, Inventory, Size, Colour
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order
from apps.payments.models import Payment

class CheckoutAndOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email='buyer@example.com', password='Password123!')
        self.address = Address.objects.create(
            user=self.user,
            full_name='Buyer Test',
            phone_number='9876543210',
            street_address='100 MG Road',
            city='Bengaluru',
            state='Karnataka',
            postal_code='560001',
            country='India',
            is_default=True
        )
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        self.product = Product.objects.create(
            title='Leather Loafers',
            slug='leather-loafers',
            category=self.category,
            base_price=Decimal('5000.00'),
            is_active=True
        )
        self.size = Size.objects.create(name='UK 7')
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size=self.size,
            sku='SH-LFR-7',
            is_active=True
        )
        self.inventory = Inventory.objects.create(
            variant=self.variant,
            stock_quantity=5,
            reserved_quantity=0
        )

    def test_complete_checkout_payment_and_inventory_reduction(self):
        self.client.force_authenticate(user=self.user)
        # Add to cart
        self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 2})

        # Validate checkout
        res_val = self.client.post('/api/checkout/validate/', {'address_id': self.address.id})
        self.assertEqual(res_val.status_code, status.HTTP_200_OK)

        # Create Order
        res_order = self.client.post('/api/orders/create/', {'address_id': self.address.id})
        self.assertEqual(res_order.status_code, status.HTTP_201_CREATED)
        self.assertIn('razorpay_order_id', res_order.data)
        rzp_order_id = res_order.data['razorpay_order_id']
        order_number = res_order.data['order_number']

        # Verify stock before payment
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 5)

        # Generate authentic HMAC signature
        rzp_payment_id = 'pay_test_99887766'
        msg = f"{rzp_order_id}|{rzp_payment_id}".encode('utf-8')
        signature = hmac.new(settings.RAZORPAY_KEY_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()

        # Submit verification
        res_verify = self.client.post('/api/payments/verify/', {
            'razorpay_order_id': rzp_order_id,
            'razorpay_payment_id': rzp_payment_id,
            'razorpay_signature': signature
        })
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertEqual(res_verify.data['order']['status'], 'confirmed')

        # Verify inventory has been decremented atomically from 5 to 3
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 3)

        # Verify user cart is cleared
        cart = Cart.objects.filter(user=self.user).first()
        self.assertTrue(cart is None or not cart.items.exists())

        # Duplicate payment verification test
        res_dup = self.client.post('/api/payments/verify/', {
            'razorpay_order_id': rzp_order_id,
            'razorpay_payment_id': rzp_payment_id,
            'razorpay_signature': signature
        })
        self.assertEqual(res_dup.status_code, status.HTTP_200_OK)
        # Inventory should NOT decrement twice
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 3)

    def test_invalid_signature_fails_payment(self):
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 1})
        res_order = self.client.post('/api/orders/create/', {'address_id': self.address.id})
        rzp_order_id = res_order.data['razorpay_order_id']

        # Tampered signature
        res_verify = self.client.post('/api/payments/verify/', {
            'razorpay_order_id': rzp_order_id,
            'razorpay_payment_id': 'pay_fake_123',
            'razorpay_signature': 'tampered_bad_signature_hash'
        })
        self.assertEqual(res_verify.status_code, status.HTTP_400_BAD_REQUEST)

        # Inventory unchanged
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 5)

    def test_cash_on_delivery_order_creation_and_inventory_reduction(self):
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 2})

        # Place COD order
        res_order = self.client.post('/api/orders/create/', {
            'address_id': self.address.id,
            'shipping_method': 'Cash on Delivery',
            'payment_method': 'cod'
        })
        self.assertEqual(res_order.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_order.data.get('cod'))
        self.assertEqual(res_order.data.get('status'), 'confirmed')

        order_number = res_order.data['order_number']
        order = Order.objects.get(order_number=order_number)
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.shipping_method, 'Cash on Delivery')
        self.assertEqual(order.payment.payment_method, 'cod')
        self.assertEqual(order.payment.status, 'pending')

        # Stock should be decremented immediately from 5 to 3
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 3)

        # Cart should be cleared
        cart = Cart.objects.filter(user=self.user).first()
        self.assertTrue(cart is None or not cart.items.exists())
