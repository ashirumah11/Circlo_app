from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for push notifications:
    - Room: user_notifications_<user_id>
    - Pushes real-time alerts when likes, comments, follows, messages occur
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        self.room_group_name = f"user_notifications_{self.user.id}"

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

    async def notification_message(self, event):
        """Forward notification payload down to the connected WebSocket client."""
        await self.send_json({
            'type': 'notification',
            'notification': event.get('notification', {}),
        })
