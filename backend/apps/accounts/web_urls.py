from django.urls import path
from .web_views import (
    LoginWebView,
    LogoutWebView,
    PasswordChangeWebView,
    PasswordResetConfirmWebView,
    PasswordResetWebView,
    RegisterWebView,
)

app_name = 'accounts-web'

urlpatterns = [
    path('register/', RegisterWebView.as_view(), name='register'),
    path('login/', LoginWebView.as_view(), name='login'),
    path('logout/', LogoutWebView.as_view(), name='logout'),
    path('password-reset/', PasswordResetWebView.as_view(), name='password-reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmWebView.as_view(), name='password-reset-confirm'),
    path('password-change/', PasswordChangeWebView.as_view(), name='password-change'),
]
