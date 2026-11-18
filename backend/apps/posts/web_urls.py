from django.urls import path
from .web_views import (
    FeedWebView,
    PostCommentWebCreateView,
    PostCreateWebView,
    PostDeleteWebView,
    PostDetailWebView,
    PostEditWebView,
    PostLikeWebToggleView,
)

urlpatterns = [
    path('', FeedWebView.as_view(), name='feed-home'),
    path('create/', PostCreateWebView.as_view(), name='post-create-web'),
    path('<int:pk>/', PostDetailWebView.as_view(), name='post-detail-web'),
    path('<int:pk>/edit/', PostEditWebView.as_view(), name='post-edit-web'),
    path('<int:pk>/delete/', PostDeleteWebView.as_view(), name='post-delete-web'),
    path('<int:pk>/like/', PostLikeWebToggleView.as_view(), name='post-like-web'),
    path('<int:pk>/comment/', PostCommentWebCreateView.as_view(), name='post-comment-web'),
]
