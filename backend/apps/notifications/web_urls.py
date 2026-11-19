from django.urls import path
from .web_views import NotificationsWebView

app_name = 'notifications_web'

urlpatterns = [
    path('', NotificationsWebView.as_view(), name='notifications-list'),
]
