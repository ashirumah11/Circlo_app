from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from .models import Conversation
from .services import MessagingService

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class InboxWebView(View):
    """
    Renders user's direct messages inbox with active conversation threads.
    """
    template_name = 'messaging/inbox.html'

    def get(self, request):
        conversations = MessagingService.get_user_conversations(request.user)
        # Prepare decorated list with other participant and unread count
        thread_items = []
        for conv in conversations:
            other = conv.get_other_participant(request.user)
            unread_cnt = conv.get_unread_count(request.user)
            thread_items.append({
                'conversation': conv,
                'other_user': other,
                'unread_count': unread_cnt,
                'last_message': conv.last_message,
            })

        return render(request, self.template_name, {
            'thread_items': thread_items,
        })


@method_decorator(login_required, name='dispatch')
class ConversationWebView(View):
    """
    Renders individual chat conversation room with real-time WebSocket connection.
    """
    template_name = 'messaging/conversation.html'

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=request.user),
            id=conversation_id
        )
        other_user = conversation.get_other_participant(request.user)
        
        # Mark incoming messages as read when opening conversation
        MessagingService.mark_as_read(conversation, request.user)

        messages_list = conversation.messages.select_related('sender').order_by('created_at')

        # Also get all conversations for sidebar preview on wide screens
        all_conversations = MessagingService.get_user_conversations(request.user)
        thread_items = []
        for conv in all_conversations:
            thread_items.append({
                'conversation': conv,
                'other_user': conv.get_other_participant(request.user),
                'unread_count': conv.get_unread_count(request.user),
                'last_message': conv.last_message,
            })

        return render(request, self.template_name, {
            'conversation': conversation,
            'other_user': other_user,
            'messages_list': messages_list,
            'thread_items': thread_items,
        })


@method_decorator(login_required, name='dispatch')
class DirectMessageUserWebView(View):
    """
    Finds or creates a direct conversation with a given username,
    then redirects to the conversation room.
    """
    def get(self, request, username):
        target_user = get_object_or_404(User, username=username)
        if target_user == request.user:
            messages.warning(request, "You cannot message yourself.")
            return redirect('messaging_web:inbox')

        try:
            conversation = MessagingService.get_or_create_conversation(request.user, target_user)
            return redirect('messaging_web:conversation', conversation_id=conversation.id)
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
            return redirect('messaging_web:inbox')
