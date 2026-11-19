from django.urls import path
from .views import (
    ConversationDetailAPIView,
    ConversationListCreateAPIView,
    ConversationMarkReadAPIView,
    ConversationMessagesListCreateAPIView,
    UnreadMessagesCountAPIView,
)

app_name = 'messaging'

urlpatterns = [
    path('', ConversationListCreateAPIView.as_view(), name='conversation-list'),
    path('unread-count/', UnreadMessagesCountAPIView.as_view(), name='conversation-unread-count'),
    path('<int:pk>/', ConversationDetailAPIView.as_view(), name='conversation-detail'),
    path('<int:conversation_id>/messages/', ConversationMessagesListCreateAPIView.as_view(), name='conversation-messages'),
    path('<int:conversation_id>/read/', ConversationMarkReadAPIView.as_view(), name='conversation-read'),
]
