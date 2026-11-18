from typing import Any, Dict, Optional
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, QuerySet

from apps.posts.models import Hashtag, Post
from apps.social.services import SocialService

User = get_user_model()


class SearchService:
    """
    Search and discovery service layer for accounts, hashtags, and explore feed.
    """

    @staticmethod
    def search_users(query: str, viewer: Optional[User] = None, limit: int = 20) -> QuerySet[User]:
        clean = query.strip().lstrip('@')
        if not clean:
            return User.objects.none()

        qs = User.objects.filter(is_active=True).filter(
            Q(username__icontains=clean) | Q(full_name__icontains=clean)
        ).order_by('-date_joined')[:limit]
        return qs

    @staticmethod
    def search_hashtags(query: str, limit: int = 20) -> QuerySet[Hashtag]:
        clean = query.strip().lstrip('#')
        if not clean:
            return Hashtag.objects.none()

        return Hashtag.objects.filter(name__icontains=clean).annotate(
            posts_count=Count('posts')
        ).order_by('-posts_count')[:limit]

    @staticmethod
    def search_posts(query: str, viewer: Optional[User] = None, limit: int = 20) -> QuerySet[Post]:
        clean = query.strip()
        if not clean:
            return Post.objects.none()

        qs = Post.objects.filter(author__is_active=True).filter(
            Q(caption__icontains=clean) |
            Q(location__icontains=clean) |
            Q(hashtags__name__icontains=clean.lstrip('#'))
        ).select_related('author').prefetch_related('media', 'likes', 'comments').distinct().order_by('-created_at')[:limit]
        return qs

    @classmethod
    def unified_search(cls, query: str, viewer: Optional[User] = None) -> Dict[str, Any]:
        """Runs search across users, hashtags, and posts."""
        clean = query.strip()
        if not clean:
            return {'users': [], 'hashtags': [], 'posts': []}

        return {
            'query': clean,
            'users': cls.search_users(clean, viewer=viewer, limit=10),
            'hashtags': cls.search_hashtags(clean, limit=10),
            'posts': cls.search_posts(clean, viewer=viewer, limit=20),
        }

    @staticmethod
    def get_explore_posts(viewer: Optional[User] = None, limit: int = 40) -> QuerySet[Post]:
        """
        Returns posts for the Explore discovery grid.
        Annotates total engagement (likes + comments) to surface trending content.
        Excludes private accounts unless the viewer is an approved follower.
        """
        qs = Post.objects.filter(author__is_active=True)

        # Exclude private accounts if viewer is not follower
        if not viewer or not viewer.is_authenticated:
            qs = qs.filter(author__is_private=False)
        else:
            # Allow public authors OR authors where viewer is an approved follower OR author is self
            followed_ids = viewer.following_relations.filter(is_pending=False).values_list('following_id', flat=True)
            qs = qs.filter(
                Q(author__is_private=False) |
                Q(author_id__in=followed_ids) |
                Q(author=viewer)
            )

        return qs.annotate(
            total_engagement=Count('likes', distinct=True) + Count('comments', distinct=True)
        ).select_related('author').prefetch_related('media').order_by('-total_engagement', '-created_at')[:limit]
