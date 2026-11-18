from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ChangePasswordAPIView,
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    RegisterAPIView,
)

app_name = 'accounts'

urlpatterns = [
    # Registration & Sessions
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),

    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Current Authenticated User
    path('me/', CurrentUserAPIView.as_view(), name='me'),

    # Password Management
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
]
