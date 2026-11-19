from django.urls import path
from .web_views import (
    ConversationWebView,
    DirectMessageUserWebView,
    InboxWebView,
)

app_name = 'messaging_web'

urlpatterns = [
    path('', InboxWebView.as_view(), name='inbox'),
    path('new/<str:username>/', DirectMessageUserWebView.as_view(), name='direct-message-user'),
    path('<int:conversation_id>/', ConversationWebView.as_view(), name='conversation'),
]
