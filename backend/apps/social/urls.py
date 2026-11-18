from django.urls import path
from .views import (
    AcceptFollowRequestAPIView,
    BlockedUsersListAPIView,
    PendingFollowRequestsAPIView,
    RejectFollowRequestAPIView,
)

app_name = 'social'

urlpatterns = [
    path('requests/', PendingFollowRequestsAPIView.as_view(), name='pending-requests'),
    path('requests/<int:pk>/accept/', AcceptFollowRequestAPIView.as_view(), name='accept-request'),
    path('requests/<int:pk>/reject/', RejectFollowRequestAPIView.as_view(), name='reject-request'),
    path('blocked/', BlockedUsersListAPIView.as_view(), name='blocked-users'),
]
