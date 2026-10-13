from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Size, Colour, Product, ProductImage, ProductVariant, Inventory, HomeBanner, AuditLog

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'display_order')

class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    fields = ('stock_quantity', 'reserved_quantity', 'low_stock_threshold')

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('sku', 'size', 'colour', 'price_override', 'is_active')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'display_order', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order')

@admin.register(Colour)
class ColourAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'color_badge')

    def color_badge(self, obj):
        return format_html(
            '<div style="width:24px;height:24px;background-color:{};border:1px solid #ddd;border-radius:4px;"></div>',
            obj.hex_code
        )
    color_badge.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'brand', 'base_price', 'discount_price', 'is_featured', 'is_new_arrival', 'is_active', 'total_sold')
    list_filter = ('is_active', 'is_featured', 'is_new_arrival', 'gender', 'category', 'brand')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'size', 'colour', 'price_override', 'is_active')
    list_filter = ('is_active', 'size', 'colour')
    search_fields = ('sku', 'product__title')
    inlines = [InventoryInline]

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('variant', 'stock_quantity', 'reserved_quantity', 'available_stock', 'is_in_stock', 'is_low_stock')
    search_fields = ('variant__sku', 'variant__product__title')

@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_text', 'button_text', 'link_url', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('object_id', 'action', 'user__email')
    readonly_fields = ('created_at', 'user', 'action', 'model_name', 'object_id', 'changes_json', 'ip_address')
