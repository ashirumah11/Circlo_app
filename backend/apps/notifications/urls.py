from django.urls import path
from .views import (
    NotificationDetailAPIView,
    NotificationListAPIView,
    NotificationReadAllAPIView,
    NotificationUnreadCountAPIView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('read-all/', NotificationReadAllAPIView.as_view(), name='notification-read-all'),
    path('unread-count/', NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),
    path('<int:pk>/', NotificationDetailAPIView.as_view(), name='notification-detail'),
]
