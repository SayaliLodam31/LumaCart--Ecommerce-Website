from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import CustomUser
from apps.catalog.models import Category, Brand, Product, ProductVariant, Inventory, Size, Colour
from apps.cart.models import Cart, CartItem, Coupon

class CartAndCouponTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email='cartuser@example.com', password='Password123!')
        
        self.category = Category.objects.create(name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            title='Linen Shirt',
            slug='linen-shirt',
            category=self.category,
            base_price=Decimal('2000.00'),
            is_active=True
        )
        self.size = Size.objects.create(name='M')
        self.colour = Colour.objects.create(name='Ivory', hex_code='#FAF9F6')
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size=self.size,
            colour=self.colour,
            sku='LMC-SHT-M',
            is_active=True
        )
        self.inventory = Inventory.objects.create(
            variant=self.variant,
            stock_quantity=10,
            reserved_quantity=0
        )
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            min_purchase=Decimal('1000.00'),
            valid_to=timezone.now() + timezone.timedelta(days=30),
            is_active=True
        )

    def test_add_item_to_cart_and_totals(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 2})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['cart']['total_items_count'], 2)
        self.assertEqual(Decimal(str(res.data['cart']['subtotal'])), Decimal('4000.00'))

    def test_stock_validation_prevents_excess_quantity(self):
        self.client.force_authenticate(user=self.user)
        # Attempt to add 15 items when only 10 in stock
        res = self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 15})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only 10 units available', res.data['error'])

    def test_apply_and_remove_coupon(self):
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 1}) # 2000 subtotal
        
        # Apply valid coupon
        res = self.client.post('/api/cart/apply-coupon/', {'code': 'SAVE10'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(res.data['cart']['discount_amount'])), Decimal('200.00')) # 10% of 2000

        # Remove coupon
        res_remove = self.client.post('/api/cart/remove-coupon/')
        self.assertEqual(res_remove.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(res_remove.data['cart']['discount_amount'])), Decimal('0.00'))

    def test_guest_cart_merges_into_user_cart(self):
        # 1. Guest adds item
        guest_client = APIClient()
        guest_headers = {'HTTP_X_SESSION_KEY': 'guest-session-uuid-1234'}
        res = guest_client.post('/api/cart/items/', {'variant_id': self.variant.id, 'quantity': 3}, **guest_headers)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # 2. User logs in and calls merge
        auth_client = APIClient()
        auth_client.force_authenticate(user=self.user)
        merge_res = auth_client.post('/api/cart/merge/', {'session_key': 'guest-session-uuid-1234'})
        self.assertEqual(merge_res.status_code, status.HTTP_200_OK)
        self.assertEqual(merge_res.data['cart']['total_items_count'], 3)
