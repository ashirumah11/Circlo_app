from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint


class Bookmark(models.Model):
    """
    Represents a saved post bookmarked by a user for later viewing.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='User'
    )
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='Post'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['user', 'post'],
                name='unique_user_post_bookmark'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"@{self.user.username} saved post #{self.post_id}"
