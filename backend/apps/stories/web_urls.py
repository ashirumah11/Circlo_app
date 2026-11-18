from django.urls import path
from .web_views import StoryCreateWebView, StoryViewerWebView

app_name = 'stories-web'

urlpatterns = [
    path('create/', StoryCreateWebView.as_view(), name='story-create'),
    path('@<str:username>/', StoryViewerWebView.as_view(), name='story-viewer'),
    path('<str:username>/', StoryViewerWebView.as_view(), name='story-viewer-alt'),
]
