from rest_framework import serializers
from .models import ProductReview

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    is_verified_buyer = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ('id', 'product', 'user', 'user_name', 'rating', 'title', 'comment', 'is_verified_buyer', 'created_at', 'created_at_formatted')
        read_only_fields = ('id', 'product', 'user', 'created_at')

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name[:1]}." if obj.user.last_name else (obj.user.first_name or "Verified Customer")

    def get_is_verified_buyer(self, obj):
        return obj.order_item is not None

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d %b %Y')
