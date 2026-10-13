from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.catalog.models import Product
from apps.orders.models import OrderItem

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150)
    comment = models.TextField()
    is_moderated = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'order_item')

    def __str__(self):
        return f"{self.rating} stars by {self.user.email} for {self.product.title}"
