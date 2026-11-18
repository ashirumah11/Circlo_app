from django.urls import path
from .web_views import BookmarkToggleWebView, SavedPostsWebView

app_name = 'bookmarks-web'

urlpatterns = [
    path('saved/', SavedPostsWebView.as_view(), name='saved-posts'),
    path('toggle/<int:pk>/', BookmarkToggleWebView.as_view(), name='toggle-bookmark'),
]
