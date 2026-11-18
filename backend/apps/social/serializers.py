from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Follow
from apps.accounts.serializers import UserSummarySerializer

User = get_user_model()


class FollowRequestSerializer(serializers.ModelSerializer):
    """Serializer for pending incoming follow requests."""
    follower = UserSummarySerializer(read_only=True)

    class Meta:
        model = Follow
        fields = [
            'id',
            'follower',
            'created_at',
            'is_pending',
        ]
