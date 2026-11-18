from django.urls import path
from .views import (
    ProfileBlockToggleAPIView,
    ProfileDetailAPIView,
    ProfileFollowersAPIView,
    ProfileFollowingAPIView,
    ProfileFollowToggleAPIView,
    ProfileListAPIView,
)

app_name = 'profiles'

urlpatterns = [
    path('', ProfileListAPIView.as_view(), name='profile-list'),
    path('<str:id>/', ProfileDetailAPIView.as_view(), name='profile-detail'),
    path('<str:id>/followers/', ProfileFollowersAPIView.as_view(), name='profile-followers'),
    path('<str:id>/following/', ProfileFollowingAPIView.as_view(), name='profile-following'),
    path('<str:id>/follow/', ProfileFollowToggleAPIView.as_view(), name='profile-follow-toggle'),
    path('<str:id>/block/', ProfileBlockToggleAPIView.as_view(), name='profile-block-toggle'),
]
