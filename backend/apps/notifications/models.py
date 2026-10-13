from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order_status', 'Order Status Update'),
        ('stock_alert', 'Stock Alert'),
        ('price_drop', 'Price Drop'),
        ('promotion', 'Promotional Offer'),
        ('system', 'System Message'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='order_status')
    is_read = models.BooleanField(default=False, db_index=True)
    data_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.email}"
