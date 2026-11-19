from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    Represents a direct one-to-one conversation between two users.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name='Participants'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        usernames = ", ".join(u.username for u in self.participants.all()[:2])
        return f"Conversation #{self.id} ({usernames})"

    def get_other_participant(self, user):
        """Returns the other user in a 1-to-1 conversation."""
        return self.participants.exclude(id=user.id).first()

    @property
    def last_message(self):
        """Returns the most recent message in the conversation."""
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user) -> int:
        """Returns count of unread messages sent by the other participant."""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """
    Represents an individual text or image message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Sender'
    )
    text = models.TextField(
        blank=True,
        verbose_name='Message Text'
    )
    image = models.ImageField(
        upload_to='messages/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Image Attachment'
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Is Read'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Read At'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Sent At'
    )

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['conversation', 'is_read']),
        ]

    def __str__(self):
        return f"Message #{self.id} from @{self.sender.username} in #{self.conversation_id}"

    @property
    def image_url(self) -> str:
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return ''
