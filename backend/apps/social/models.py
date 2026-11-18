from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint


class Follow(models.Model):
    """
    Represents a following connection or follow request between two users.
    - If target user is public: is_pending = False (active follow)
    - If target user is private: is_pending = True until accepted by target
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_relations',
        verbose_name='Follower'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_relations',
        verbose_name='Following'
    )
    is_pending = models.BooleanField(
        default=False,
        help_text='True when waiting for target user of private account to approve.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follow_relation'
            ),
            CheckConstraint(
                condition=~Q(follower=F('following')),
                name='prevent_self_follow'
            )
        ]
        indexes = [
            models.Index(fields=['follower', 'is_pending']),
            models.Index(fields=['following', 'is_pending']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        super().clean()
        if self.follower_id and self.following_id and self.follower_id == self.following_id:
            raise ValidationError('Users cannot follow themselves.')

    def __str__(self):
        status = "pending" if self.is_pending else "active"
        return f"@{self.follower.username} -> @{self.following.username} ({status})"


class Block(models.Model):
    """
    Represents a blocking relationship.
    When user A blocks user B:
    - Any existing follow connection between them is severed.
    - Neither can view each other's profiles, posts, comments, or stories.
    """
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocking_relations',
        verbose_name='Blocker'
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocked_by_relations',
        verbose_name='Blocked User'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Block'
        verbose_name_plural = 'Blocks'
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['blocker', 'blocked'],
                name='unique_block_relation'
            ),
            CheckConstraint(
                condition=~Q(blocker=F('blocked')),
                name='prevent_self_block'
            )
        ]

    def clean(self):
        super().clean()
        if self.blocker_id and self.blocked_id and self.blocker_id == self.blocked_id:
            raise ValidationError('Users cannot block themselves.')

    def __str__(self):
        return f"@{self.blocker.username} blocked @{self.blocked.username}"


class Mute(models.Model):
    """
    Represents a muting relationship.
    Hides posts/stories from muted user in the feed without unfollowing.
    """
    muter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='muting_relations',
        verbose_name='Muter'
    )
    muted = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='muted_by_relations',
        verbose_name='Muted User'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mute'
        verbose_name_plural = 'Mutes'
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['muter', 'muted'],
                name='unique_mute_relation'
            ),
            CheckConstraint(
                condition=~Q(muter=F('muted')),
                name='prevent_self_mute'
            )
        ]

    def clean(self):
        super().clean()
        if self.muter_id and self.muted_id and self.muter_id == self.muted_id:
            raise ValidationError('Users cannot mute themselves.')

    def __str__(self):
        return f"@{self.muter.username} muted @{self.muted.username}"
