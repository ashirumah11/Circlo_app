from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation
from .services import MessagingService

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer handling real-time direct chat between participants:
    - Room: chat_<conversation_id>
    - Handles message broadcasting, typing indicators, and read receipts
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        # Ensure user belongs to this conversation
        is_participant = await self._is_participant(self.conversation_id, self.user)
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        action = content.get('action')

        if action == 'send_message':
            text = content.get('text', '').strip()
            if text:
                # Save message and let service trigger broadcast
                await self._save_message(self.conversation_id, self.user, text)

        elif action == 'typing':
            is_typing = bool(content.get('is_typing', True))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing,
                }
            )

        elif action == 'mark_read':
            await self._mark_read(self.conversation_id, self.user)

    # Handlers for messages forwarded from channel layer
    async def chat_message(self, event):
        await self.send_json({
            'type': 'chat_message',
            'message': event.get('message', {}),
        })

    async def typing_status(self, event):
        # Don't echo typing status back to the typing user
        if event.get('user_id') != self.user.id:
            await self.send_json({
                'type': 'typing_status',
                'user_id': event.get('user_id'),
                'username': event.get('username'),
                'is_typing': event.get('is_typing'),
            })

    async def messages_read(self, event):
        await self.send_json({
            'type': 'messages_read',
            'read_by_id': event.get('read_by_id'),
            'read_at': event.get('read_at'),
        })

    @database_sync_to_async
    def _is_participant(self, conversation_id: int, user: User) -> bool:
        return Conversation.objects.filter(id=conversation_id, participants=user).exists()

    @database_sync_to_async
    def _save_message(self, conversation_id: int, sender: User, text: str):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            MessagingService.send_message(conversation=conversation, sender=sender, text=text)
        except Exception:
            pass

    @database_sync_to_async
    def _mark_read(self, conversation_id: int, user: User):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            MessagingService.mark_as_read(conversation=conversation, user=user)
        except Exception:
            pass
