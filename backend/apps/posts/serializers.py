from rest_framework import serializers
from .models import Hashtag, Post, PostMedia
from apps.accounts.serializers import UserSummarySerializer


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']


class PostMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.ReadOnlyField()

    class Meta:
        model = PostMedia
        fields = ['id', 'file', 'file_url', 'media_type', 'order']


class PostSerializer(serializers.ModelSerializer):
    """Complete post representation with author profile, media carousel, and engagement stats."""
    author = UserSummarySerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    hashtags = serializers.StringRelatedField(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'caption',
            'location',
            'media',
            'hashtags',
            'likes_count',
            'comments_count',
            'is_liked',
            'is_bookmarked',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_is_liked(self, obj: Post) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_bookmarked(self, obj: Post) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()


class PostCreateSerializer(serializers.ModelSerializer):
    """Handles creating a new post with uploaded photos or videos."""
    media = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True,
        help_text="One or more images or videos."
    )

    class Meta:
        model = Post
        fields = ['id', 'caption', 'location', 'media']
        extra_kwargs = {
            'caption': {'required': False},
            'location': {'required': False},
        }
