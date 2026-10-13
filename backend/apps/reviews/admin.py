from django.contrib import admin
from .models import ProductReview

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_moderated', 'created_at')
    list_filter = ('rating', 'is_moderated', 'created_at')
    list_editable = ('is_moderated',)
    search_fields = ('title', 'comment', 'product__title', 'user__email')
