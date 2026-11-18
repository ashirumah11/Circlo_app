from django.urls import path
from .views import (
    StoriesListCreateAPIView,
    StoryDetailAPIView,
    StoryRecordViewAPIView,
    StoryViewersListAPIView,
)

app_name = 'stories'

urlpatterns = [
    path('', StoriesListCreateAPIView.as_view(), name='stories-list-create'),
    path('<int:pk>/', StoryDetailAPIView.as_view(), name='story-detail'),
    path('<int:pk>/view/', StoryRecordViewAPIView.as_view(), name='story-record-view'),
    path('<int:pk>/viewers/', StoryViewersListAPIView.as_view(), name='story-viewers'),
]
