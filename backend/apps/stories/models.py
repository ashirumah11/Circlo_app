from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone


def default_story_expiry():
    return timezone.now() + timedelta(hours=24)


class Story(models.Model):
    """
    Ephemeral 24-hour photo or video story.
    Expires automatically 24 hours after creation.
    """
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories',
        verbose_name='Story Author'
    )
    media_file = models.FileField(
        upload_to='stories/%Y/%m/%d/',
        verbose_name='Story Media'
    )
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        default='image'
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Caption'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    expires_at = models.DateTimeField(
        default=default_story_expiry,
        db_index=True
    )

    class Meta:
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['author', 'expires_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Story #{self.id} by @{self.author.username} ({self.media_type})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_video(self) -> bool:
        return self.media_type == 'video'

    @property
    def file_url(self) -> str:
        if self.media_file and hasattr(self.media_file, 'url'):
            return self.media_file.url
        return ''

    @property
    def views_count(self) -> int:
        return self.views.count()


class StoryView(models.Model):
    """
    Tracks who viewed a story, ensuring unique view records per viewer per story.
    """
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Story'
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='story_views',
        verbose_name='Viewer'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Story View'
        verbose_name_plural = 'Story Views'
        ordering = ['-viewed_at']
        constraints = [
            UniqueConstraint(
                fields=['story', 'viewer'],
                name='unique_story_viewer'
            )
        ]
        indexes = [
            models.Index(fields=['story', 'viewed_at']),
        ]

    def __str__(self):
        return f"@{self.viewer.username} viewed Story #{self.story_id}"
