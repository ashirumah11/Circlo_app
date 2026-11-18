from typing import Tuple
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import Bookmark
from apps.posts.models import Post

User = get_user_model()


class BookmarkService:
    """
    Business service layer managing user post bookmarks / saved items.
    """

    @staticmethod
    def toggle_bookmark(user: User, post: Post) -> Tuple[bool, str]:
        """
        Toggles saving/bookmarking a post for a user.
        Returns: (is_bookmarked: bool, message: str)
        """
        bookmark = Bookmark.objects.filter(user=user, post=post).first()
        if bookmark:
            bookmark.delete()
            return False, "Post removed from your saved posts."

        Bookmark.objects.create(user=user, post=post)
        return True, "Post saved to your collection."

    @staticmethod
    def is_bookmarked(user: User, post: Post) -> bool:
        """Checks if user has saved this post."""
        if not user or not user.is_authenticated:
            return False
        return Bookmark.objects.filter(user=user, post=post).exists()

    @staticmethod
    def get_user_bookmarked_posts(user: User) -> QuerySet[Post]:
        """
        Returns QuerySet of Post objects saved by the user, ordered latest first.
        """
        return Post.objects.filter(
            bookmarks__user=user,
            author__is_active=True
        ).select_related('author').prefetch_related('media', 'likes', 'comments').order_by('-bookmarks__created_at')
