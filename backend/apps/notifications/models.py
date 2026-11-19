from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    User notification triggered by interactions:
    follows, requests, likes, comments, replies, stories, and messages.
    """
    NOTIFICATION_TYPES = (
        ('follow', 'New Follower'),
        ('follow_request', 'Follow Request'),
        ('like_post', 'Post Liked'),
        ('like_comment', 'Comment Liked'),
        ('comment', 'New Comment'),
        ('reply', 'Comment Reply'),
        ('story_view', 'Story View'),
        ('message', 'Direct Message'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Recipient'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='caused_notifications',
        verbose_name='Actor'
    )
    verb = models.CharField(
        max_length=32,
        choices=NOTIFICATION_TYPES,
        verbose_name='Action Type'
    )
    target_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Target Entity ID'
    )
    target_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Target URL'
    )
    text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Notification Message'
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Is Read'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for @{self.recipient.username}: @{self.actor.username} {self.verb}"
