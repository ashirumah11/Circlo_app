from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
    StartConversationSerializer,
)
from .services import MessagingService

User = get_user_model()


class ConversationListCreateAPIView(generics.ListCreateAPIView):
    """
    List user's active conversations or initiate a conversation with another user.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MessagingService.get_user_conversations(self.request.user)

    @extend_schema(
        summary="List user conversations",
        responses={200: ConversationSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Start or get existing conversation",
        request=StartConversationSerializer,
        responses={200: ConversationSerializer, 201: ConversationSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_id = serializer.validated_data.get('recipient_id')
        recipient_username = serializer.validated_data.get('recipient_username')

        if recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
        else:
            recipient = get_object_or_404(User, username=recipient_username)

        try:
            conversation = MessagingService.get_or_create_conversation(request.user, recipient)
        except ValidationError as e:
            return Response({'detail': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class ConversationDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve details of a single conversation.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    @extend_schema(
        summary="Retrieve conversation details",
        responses={200: ConversationSerializer, 404: OpenApiResponse(description="Not found")}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ConversationMessagesListCreateAPIView(APIView):
    """
    List messages in a conversation or send a new message.
    Supports JSON and multipart form data (for image attachments).
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_conversation(self, conversation_id: int, user: User) -> Conversation:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")
        return conversation

    @extend_schema(
        summary="List messages in a conversation",
        responses={200: MessageSerializer(many=True)}
    )
    def get(self, request, conversation_id, *args, **kwargs):
        conversation = self._get_conversation(conversation_id, request.user)
        messages = conversation.messages.select_related('sender').order_by('created_at')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Send message in conversation",
        request=SendMessageSerializer,
        responses={201: MessageSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request, conversation_id, *args, **kwargs):
        conversation = self._get_conversation(conversation_id, request.user)
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data.get('text', '')
        image = serializer.validated_data.get('image', None)

        try:
            message = MessagingService.send_message(
                conversation=conversation,
                sender=request.user,
                text=text,
                image=image
            )
        except ValidationError as e:
            return Response({'detail': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class ConversationMarkReadAPIView(APIView):
    """
    Mark all unread incoming messages in a conversation as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Mark conversation as read",
        responses={200: OpenApiResponse(description="Marked as read")}
    )
    def post(self, request, conversation_id, *args, **kwargs):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")

        updated_count = MessagingService.mark_as_read(conversation, request.user)
        return Response({
            'message': f"Marked {updated_count} messages as read.",
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)


class UnreadMessagesCountAPIView(APIView):
    """
    Get unread messages count for the authenticated user (for badge counters).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get unread messages count",
        responses={200: OpenApiResponse(description="Unread messages count")}
    )
    def get(self, request, *args, **kwargs):
        count = MessagingService.get_unread_count(request.user)
        return Response({'unread_count': count}, status=status.HTTP_200_OK)
