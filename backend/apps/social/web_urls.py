from django.urls import path
from .web_views import (
    FollowRequestActionWebView,
    FollowRequestsWebView,
    FollowToggleWebView,
)

app_name = 'social-web'

urlpatterns = [
    path('follow/<int:pk>/', FollowToggleWebView.as_view(), name='follow-toggle'),
    path('requests/', FollowRequestsWebView.as_view(), name='follow-requests'),
    path('requests/<int:pk>/action/', FollowRequestActionWebView.as_view(), name='follow-request-action'),
]
