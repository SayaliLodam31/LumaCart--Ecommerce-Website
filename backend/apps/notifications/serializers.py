from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'notification_type', 'is_read', 'data_json', 'created_at', 'created_at_formatted')

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d %b, %I:%M %p')
