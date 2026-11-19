from typing import Optional
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from .models import Conversation, Message
from apps.notifications.services import NotificationService
from apps.social.services import SocialService

User = get_user_model()


class MessagingService:
    """
    Business service layer managing direct 1-to-1 conversations:
    - Conversation lookup and creation
    - Message sending with text and image attachments
    - Real-time WebSocket broadcasting via Channels
    - Read receipts and unread counters
    """

    @classmethod
    def get_or_create_conversation(cls, user_a: User, user_b: User) -> Conversation:
        if user_a.id == user_b.id:
            raise ValidationError("You cannot create a conversation with yourself.")

        if SocialService.is_blocked(user_a, user_b):
            raise ValidationError("Cannot start conversation with this user.")

        # Find existing conversation with exactly these two participants
        conversation = (
            Conversation.objects.filter(participants=user_a)
            .filter(participants=user_b)
            .annotate(num_participants=Count('participants'))
            .filter(num_participants=2)
            .first()
        )

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(user_a, user_b)

        return conversation

    @staticmethod
    def get_user_conversations(user: User) -> QuerySet[Conversation]:
        return (
            Conversation.objects.filter(participants=user)
            .prefetch_related('participants', 'messages__sender')
            .order_by('-updated_at')
        )

    @classmethod
    def send_message(
        cls,
        conversation: Conversation,
        sender: User,
        text: str = "",
        image=None
    ) -> Message:
        if sender not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")

        recipient = conversation.get_other_participant(sender)
        if not recipient:
            raise ValidationError("No recipient found in this conversation.")

        if SocialService.is_blocked(sender, recipient):
            raise ValidationError("Cannot message this user.")

        clean_text = text.strip() if text else ""
        if not clean_text and not image:
            raise ValidationError("Message must contain text or an image attachment.")

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            text=clean_text,
            image=image
        )

        # Update conversation timestamp so it jumps to top of inbox
        conversation.save(update_fields=['updated_at'])

        # Broadcast via WebSocket to the conversation room
        cls.broadcast_message(message)

        # Send notification to recipient
        preview_text = clean_text[:40] if clean_text else "Sent an image"
        NotificationService.create_notification(
            recipient=recipient,
            actor=sender,
            verb='message',
            text=preview_text,
            target_id=conversation.id,
            target_url=f"/messages/{conversation.id}/"
        )

        return message

    @staticmethod
    def broadcast_message(message: Message):
        """Broadcasts newly created message to WebSocket conversation room."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                from .serializers import MessageSerializer
                payload = MessageSerializer(message).data
                async_to_sync(channel_layer.group_send)(
                    f"chat_{message.conversation_id}",
                    {
                        'type': 'chat_message',
                        'message': payload,
                    }
                )
        except Exception:
            pass

    @classmethod
    def mark_as_read(cls, conversation: Conversation, user: User) -> int:
        """
        Marks unread messages sent by the other participant as read.
        Broadcasts read receipt event to room.
        """
        now = timezone.now()
        unread_qs = conversation.messages.filter(is_read=False).exclude(sender=user)
        updated_count = unread_qs.update(is_read=True, read_at=now)

        if updated_count > 0:
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"chat_{conversation.id}",
                        {
                            'type': 'messages_read',
                            'read_by_id': user.id,
                            'read_at': now.isoformat(),
                        }
                    )
            except Exception:
                pass

        return updated_count

    @staticmethod
    def get_unread_count(user: User) -> int:
        if not user or not user.is_authenticated:
            return 0
        return (
            Message.objects.filter(
                conversation__participants=user,
                is_read=False
            )
            .exclude(sender=user)
            .count()
        )
