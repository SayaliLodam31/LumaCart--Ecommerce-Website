from rest_framework import serializers
from .models import Category, Brand, Size, Colour, Product, ProductImage, ProductVariant, Inventory, HomeBanner, AuditLog, Wishlist, WishlistItem

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'is_active', 'display_order', 'product_count')

class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'logo', 'description', 'is_active', 'product_count')

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('id', 'name', 'sort_order')

class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = ('id', 'name', 'hex_code')

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'image_url', 'alt_text', 'is_primary', 'display_order')

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        if hasattr(obj, 'image_url') and obj.image_url:
            return obj.image_url
        return None

class InventorySerializer(serializers.ModelSerializer):
    available_stock = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventory
        fields = ('stock_quantity', 'reserved_quantity', 'available_stock', 'is_in_stock', 'is_low_stock')

class ProductVariantSerializer(serializers.ModelSerializer):
    size_name = serializers.CharField(source='size.name', read_only=True)
    colour_name = serializers.CharField(source='colour.name', read_only=True)
    colour_hex = serializers.CharField(source='colour.hex_code', read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    stock = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            'id', 'sku', 'size', 'size_name', 'colour', 'colour_name', 'colour_hex',
            'price_override', 'effective_price', 'stock', 'is_in_stock', 'is_active'
        )

    def get_stock(self, obj):
        if hasattr(obj, 'inventory'):
            return obj.inventory.available_stock
        return 0

    def get_is_in_stock(self, obj):
        return self.get_stock(obj) > 0

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    available_sizes = serializers.SerializerMethodField()
    available_colours = serializers.SerializerMethodField()
    total_stock = serializers.IntegerField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category', 'category_name', 'category_slug',
            'brand', 'brand_name', 'gender', 'base_price', 'discount_price',
            'current_price', 'primary_image', 'available_sizes', 'available_colours',
            'is_featured', 'is_new_arrival', 'total_sold', 'total_stock',
            'average_rating', 'reviews_count', 'created_at'
        )

    def get_primary_image(self, obj):
        request = self.context.get('request')
        images = list(obj.images.all())
        primary = next((img for img in images if img.is_primary), None) or (images[0] if images else None)
        if primary:
            if primary.image:
                return request.build_absolute_uri(primary.image.url) if request else primary.image.url
            if hasattr(primary, 'image_url') and primary.image_url:
                return primary.image_url
        return None

    def get_available_sizes(self, obj):
        sizes = set()
        variants = [v for v in obj.variants.all() if v.is_active]
        for variant in variants:
            if variant.size and hasattr(variant, 'inventory') and variant.inventory.available_stock > 0:
                sizes.add(variant.size.name)
        return list(sizes)

    def get_available_colours(self, obj):
        colours = []
        seen = set()
        variants = [v for v in obj.variants.all() if v.is_active]
        for variant in variants:
            if variant.colour and variant.colour.id not in seen:
                if hasattr(variant, 'inventory') and variant.inventory.available_stock > 0:
                    seen.add(variant.colour.id)
                    colours.append({'id': variant.colour.id, 'name': variant.colour.name, 'hex': variant.colour.hex_code})
        return colours

    def get_average_rating(self, obj):
        if hasattr(obj, 'reviews'):
            reviews = [r for r in obj.reviews.all() if r.is_moderated]
            if reviews:
                return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 5.0

    def get_reviews_count(self, obj):
        if hasattr(obj, 'reviews'):
            return sum(1 for r in obj.reviews.all() if r.is_moderated)
        return 0

class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ('description', 'images', 'variants', 'related_products')

    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category,
            is_active=True
        ).exclude(id=obj.id).select_related('category', 'brand').prefetch_related('images', 'variants__size', 'variants__colour', 'variants__inventory', 'reviews')[:4]
        return ProductListSerializer(related, many=True, context=self.context).data


class HomeBannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HomeBanner
        fields = ('id', 'title', 'subtitle', 'badge_text', 'button_text', 'link_url', 'image', 'image_url', 'background_color', 'display_order')

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url_fallback

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'user', 'user_email', 'action', 'model_name', 'object_id', 'changes_json', 'ip_address', 'created_at')

class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_id', 'created_at')

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'items', 'count', 'updated_at')

