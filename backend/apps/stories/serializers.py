from rest_framework import serializers

from .models import Story, StoryView
from apps.accounts.serializers import UserSummarySerializer


class StorySerializer(serializers.ModelSerializer):
    """Serializer for individual story items."""
    author = UserSummarySerializer(read_only=True)
    file_url = serializers.ReadOnlyField()
    views_count = serializers.ReadOnlyField()
    is_viewed = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id',
            'author',
            'file_url',
            'media_type',
            'caption',
            'views_count',
            'is_viewed',
            'created_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'author', 'file_url', 'media_type', 'views_count', 'is_viewed', 'created_at', 'expires_at']

    def get_is_viewed(self, obj: Story) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.views.filter(viewer=request.user).exists()


class StoryGroupSerializer(serializers.Serializer):
    """Represents an author's active story bundle in the stories tray."""
    author = UserSummarySerializer()
    stories = StorySerializer(many=True)
    has_unviewed = serializers.BooleanField()
    is_self = serializers.BooleanField()


class StoryUploadSerializer(serializers.Serializer):
    """Payload for uploading a new story."""
    file = serializers.FileField(required=True)
    caption = serializers.CharField(max_length=255, required=False, allow_blank=True)


class StoryViewSerializer(serializers.ModelSerializer):
    """Represents a user who viewed a story."""
    viewer = UserSummarySerializer(read_only=True)

    class Meta:
        model = StoryView
        fields = ['id', 'viewer', 'viewed_at']
