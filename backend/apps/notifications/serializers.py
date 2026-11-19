from rest_framework import serializers

from .models import Notification
from apps.accounts.serializers import UserSummarySerializer


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications."""
    actor = UserSummarySerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'actor',
            'verb',
            'text',
            'target_id',
            'target_url',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'actor', 'verb', 'text', 'target_id', 'target_url', 'created_at']
