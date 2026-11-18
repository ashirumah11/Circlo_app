from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class Comment(TimeStampedModel):
    """
    Comment on a post. Supports nested comment replies via parent relationship.
    """
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='comments',
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    text = models.TextField(
        max_length=1000,
        help_text="Comment text up to 1,000 characters."
    )
    is_edited = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment #{self.id} by @{self.user.username} on Post #{self.post_id}"

    @property
    def is_reply(self) -> bool:
        return self.parent_id is not None

    @property
    def likes_count(self) -> int:
        return self.likes.count()

    @property
    def replies_count(self) -> int:
        return self.replies.count()


class CommentLike(TimeStampedModel):
    """User likes on comments."""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )

    class Meta:
        unique_together = ('comment', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.user.username} liked Comment #{self.comment_id}"
