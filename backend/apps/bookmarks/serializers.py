from rest_framework import serializers

from .models import Bookmark
from apps.posts.serializers import PostSerializer


class BookmarkSerializer(serializers.ModelSerializer):
    """Represents a bookmark with the nested post details."""
    post = PostSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = [
            'id',
            'post',
            'created_at',
        ]
