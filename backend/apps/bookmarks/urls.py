from django.urls import path
from .views import BookmarkListAPIView, BookmarkToggleAPIView

app_name = 'bookmarks'

urlpatterns = [
    path('', BookmarkListAPIView.as_view(), name='bookmark-list'),
    path('toggle/', BookmarkToggleAPIView.as_view(), name='bookmark-toggle'),
    path('<int:pk>/', BookmarkToggleAPIView.as_view(), name='bookmark-toggle-id'),
]
