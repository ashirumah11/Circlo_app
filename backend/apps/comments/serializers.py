from rest_framework import serializers
from .models import Comment
from apps.accounts.serializers import UserSummarySerializer


class CommentReplySerializer(serializers.ModelSerializer):
    """Serializer for nested comment replies."""
    user = UserSummarySerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'user',
            'text',
            'likes_count',
            'is_liked',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_is_liked(self, obj: Comment) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()


class CommentSerializer(serializers.ModelSerializer):
    """Complete comment representation with nested replies and like state."""
    user = UserSummarySerializer(read_only=True)
    replies = CommentReplySerializer(many=True, read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'post_id',
            'user',
            'parent_id',
            'text',
            'replies',
            'replies_count',
            'likes_count',
            'is_liked',
            'created_at',
        ]
        read_only_fields = ['id', 'post_id', 'user', 'created_at']

    def get_is_liked(self, obj: Comment) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()


class CommentCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ['text', 'parent_id']
        extra_kwargs = {
            'text': {'required': True},
        }
