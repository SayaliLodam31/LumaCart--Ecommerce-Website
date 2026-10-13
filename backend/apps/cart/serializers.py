from rest_framework import serializers
from .models import Cart, CartItem, Coupon
from apps.catalog.serializers import ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    primary_image = serializers.SerializerMethodField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    available_stock = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_title', 'product_slug', 'variant',
            'variant_details', 'primary_image', 'quantity', 'unit_price',
            'subtotal', 'available_stock'
        )
        read_only_fields = ('id', 'price_at_addition')

    def get_primary_image(self, obj):
        request = self.context.get('request')
        primary = obj.product.images.filter(is_primary=True).first() or obj.product.images.first()
        if primary and primary.image:
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None

    def get_available_stock(self, obj):
        if hasattr(obj.variant, 'inventory'):
            return obj.variant.inventory.available_stock
        return 0

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ('id', 'code', 'discount_type', 'discount_value', 'min_purchase', 'max_discount')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_charge = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'items', 'coupon', 'subtotal', 'discount_amount',
            'shipping_charge', 'tax_amount', 'total_amount', 'total_items_count'
        )
