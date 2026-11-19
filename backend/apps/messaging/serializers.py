from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from apps.accounts.serializers import UserSummarySerializer

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for individual chat messages."""
    sender = UserSummarySerializer(read_only=True)
    image_url = serializers.ReadOnlyField()

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'text',
            'image',
            'image_url',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = ['id', 'conversation', 'sender', 'is_read', 'read_at', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    """Serializer to validate sending a new message."""
    text = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        text = attrs.get('text', '').strip()
        image = attrs.get('image')
        if not text and not image:
            raise serializers.ValidationError("Either text or an image attachment is required.")
        attrs['text'] = text
        return attrs


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations with recipient summary and latest message."""
    participants = UserSummarySerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',
            'other_user',
            'last_message',
            'unread_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'participants', 'last_message', 'created_at', 'updated_at']

    def get_unread_count(self, obj) -> int:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0

    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.get_other_participant(request.user)
            if other:
                return UserSummarySerializer(other, context=self.context).data
        return None


class StartConversationSerializer(serializers.Serializer):
    """Serializer to initiate a conversation with another user."""
    recipient_id = serializers.IntegerField(required=False)
    recipient_username = serializers.CharField(required=False)

    def validate(self, attrs):
        recipient_id = attrs.get('recipient_id')
        username = attrs.get('recipient_username')
        if not recipient_id and not username:
            raise serializers.ValidationError("Either recipient_id or recipient_username must be provided.")
        return attrs
