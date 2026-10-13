from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=50, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

class Colour(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, help_text="e.g. #FAF9F6")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hex_code})"

class Product(models.Model):
    GENDER_CHOICES = (
        ('women', 'Women'),
        ('men', 'Men'),
        ('unisex', 'Unisex'),
        ('accessories', 'Accessories'),
    )

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', db_index=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', db_index=True)
    description = models.TextField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='women', db_index=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], db_index=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))])
    is_featured = models.BooleanField(default=False, db_index=True)
    is_new_arrival = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    total_sold = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.discount_price if self.discount_price is not None and self.discount_price > 0 else self.base_price

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first() or self.images.first()
        if img:
            if img.image:
                return img.image.url
            if hasattr(img, 'image_url') and img.image_url:
                return img.image_url
        return None

    @property
    def total_stock(self):
        return sum(variant.inventory.available_stock for variant in self.variants.all() if hasattr(variant, 'inventory'))

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Direct CDN or external image URL")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'display_order', 'id']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.title}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.PROTECT, null=True, blank=True, related_name='variants')
    colour = models.ForeignKey(Colour, on_delete=models.PROTECT, null=True, blank=True, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'size', 'colour')
        ordering = ['product', 'size__sort_order', 'colour__name']

    @property
    def effective_price(self):
        if self.price_override is not None and self.price_override > 0:
            return self.price_override
        return self.product.current_price

    def __str__(self):
        parts = [self.product.title]
        if self.size:
            parts.append(f"Size: {self.size.name}")
        if self.colour:
            parts.append(f"Color: {self.colour.name}")
        return " - ".join(parts)

class Inventory(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name='inventory')
    stock_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(stock_quantity__gte=0), name='stock_quantity_non_negative'),
            models.CheckConstraint(condition=models.Q(reserved_quantity__gte=0), name='reserved_quantity_non_negative'),
        ]

    @property
    def available_stock(self):
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def is_in_stock(self):
        return self.available_stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.available_stock <= self.low_stock_threshold

    def __str__(self):
        return f"{self.variant.sku}: {self.available_stock} in stock"

class HomeBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    badge_text = models.CharField(max_length=50, blank=True, default="NEW COLLECTION")
    button_text = models.CharField(max_length=50, default="Explore Now")
    link_url = models.CharField(max_length=255, default="/pages/products.html")
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    image_url_fallback = models.URLField(max_length=500, blank=True, null=True)
    background_color = models.CharField(max_length=30, default="#F8F7F4")
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.title

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    changes_json = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')}: {self.action} on {self.model_name}"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.email}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.title} in {self.wishlist.user.email}'s wishlist"

