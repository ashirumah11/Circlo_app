from django.urls import path
from apps.bookmarks.views import BookmarkToggleAPIView
from .views import (
    FeedAPIView,
    PostCommentsListCreateAPIView,
    PostDetailAPIView,
    PostLikeToggleAPIView,
    PostListCreateAPIView,
)

app_name = 'posts'

urlpatterns = [
    path('', PostListCreateAPIView.as_view(), name='post-list-create'),
    path('<int:pk>/', PostDetailAPIView.as_view(), name='post-detail'),
    path('<int:pk>/like/', PostLikeToggleAPIView.as_view(), name='post-like-toggle'),
    path('<int:pk>/bookmark/', BookmarkToggleAPIView.as_view(), name='post-bookmark-toggle'),
    path('<int:pk>/comments/', PostCommentsListCreateAPIView.as_view(), name='post-comments'),
]
