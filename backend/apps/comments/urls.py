from django.urls import path
from .views import CommentDetailAPIView, CommentLikeToggleAPIView

app_name = 'comments'

urlpatterns = [
    path('<int:pk>/', CommentDetailAPIView.as_view(), name='comment-detail'),
    path('<int:pk>/like/', CommentLikeToggleAPIView.as_view(), name='comment-like-toggle'),
]
