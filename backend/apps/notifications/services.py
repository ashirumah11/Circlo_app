from typing import Optional
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import Notification
from apps.social.services import SocialService

User = get_user_model()


class NotificationService:
    """
    Business service layer managing user notifications:
    - Creation, block checks, and real-time push via Django Channels
    - Marking single or all as read
    - Unread counters
    """

    @classmethod
    def create_notification(
        cls,
        recipient: User,
        actor: User,
        verb: str,
        text: str = "",
        target_id: Optional[int] = None,
        target_url: str = ""
    ) -> Optional[Notification]:
        # Do not notify self
        if recipient.id == actor.id:
            return None

        # Do not notify if either user has blocked the other
        if SocialService.is_blocked(actor, recipient):
            return None

        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            text=text[:255] if text else "",
            target_id=target_id,
            target_url=target_url[:255] if target_url else ""
        )

        # Broadcast via Django Channels to user's real-time group
        cls.broadcast_notification(notification)

        return notification

    @staticmethod
    def broadcast_notification(notification: Notification):
        """Pushes real-time notification to the recipient's WebSocket channel."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                from .serializers import NotificationSerializer
                payload = NotificationSerializer(notification).data
                async_to_sync(channel_layer.group_send)(
                    f"user_notifications_{notification.recipient_id}",
                    {
                        'type': 'notification_message',
                        'notification': payload,
                    }
                )
        except Exception:
            # Silently continue if channels/redis layer isn't running in synchronous context
            pass

    @staticmethod
    def get_user_notifications(user: User, unread_only: bool = False) -> QuerySet[Notification]:
        qs = Notification.objects.filter(recipient=user).select_related('actor')
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs

    @staticmethod
    def mark_as_read(notification_id: int, user: User) -> bool:
        updated = Notification.objects.filter(id=notification_id, recipient=user).update(is_read=True)
        return updated > 0

    @staticmethod
    def mark_all_as_read(user: User) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    @staticmethod
    def get_unread_count(user: User) -> int:
        if not user or not user.is_authenticated:
            return 0
        return Notification.objects.filter(recipient=user, is_read=False).count()
