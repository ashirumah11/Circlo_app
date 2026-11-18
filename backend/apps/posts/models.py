import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from apps.core.models import TimeStampedModel


class Hashtag(models.Model):
    """Stores unique hashtags extracted from post captions."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.lstrip('#').lower().strip()


class Post(TimeStampedModel):
    """
    Main post model supporting captions, locations, hashtags,
    and multiple attached photos/videos.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        db_index=True
    )
    caption = models.TextField(
        max_length=2200,
        blank=True,
        help_text="Caption text up to 2,200 characters."
    )
    location = models.CharField(
        max_length=150,
        blank=True
    )
    hashtags = models.ManyToManyField(
        Hashtag,
        related_name='posts',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post #{self.id} by @{self.author.username}"

    @property
    def likes_count(self) -> int:
        return self.likes.count()

    @property
    def comments_count(self) -> int:
        return self.comments.count()

    @property
    def primary_media(self):
        return self.media.first()


def post_media_upload_path(instance, filename):
    return f"posts/{instance.post.author_id}/{instance.post_id}/{filename}"


class PostMedia(TimeStampedModel):
    """
    Media attachments (images and videos) associated with a post.
    Supports carousels with order preservation.
    """
    MEDIA_TYPE_IMAGE = 'image'
    MEDIA_TYPE_VIDEO = 'video'
    MEDIA_TYPES = (
        (MEDIA_TYPE_IMAGE, 'Image'),
        (MEDIA_TYPE_VIDEO, 'Video'),
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media'
    )
    file = models.FileField(
        upload_to='posts/%Y/%m/%d/'
    )
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        default=MEDIA_TYPE_IMAGE
    )
    order = models.PositiveSmallIntegerField(
        default=0
    )

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Media #{self.id} ({self.media_type}) for Post #{self.post_id}"

    @property
    def is_video(self) -> bool:
        return self.media_type == self.MEDIA_TYPE_VIDEO

    @property
    def file_url(self) -> str:
        return self.file.url if self.file else ''


class PostLike(TimeStampedModel):
    """User likes on posts."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes'
    )

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.user.username} liked Post #{self.post_id}"
