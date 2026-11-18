from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from apps.posts.serializers import HashtagSerializer, PostSerializer


class UnifiedSearchResultSerializer(serializers.Serializer):
    """Unified search payload returning accounts, hashtags, and posts."""
    query = serializers.CharField()
    users = UserSummarySerializer(many=True)
    hashtags = HashtagSerializer(many=True)
    posts = PostSerializer(many=True)
