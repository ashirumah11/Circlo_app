"""
Circlo URL Configuration.

Defines all routing for:
1. Server-rendered web application templates
2. API v1 endpoints
3. OpenAPI / Swagger documentation
4. Admin panel
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import HealthCheckAPIView
from apps.posts.views import FeedAPIView
from apps.posts.web_views import FeedWebView, PostCreateWebView
from apps.profiles.web_views import (
    MyProfileRedirectWebView,
    ProfileEditWebView,
    ProfileWebView,
)
from apps.search.views import ExploreAPIView
from apps.search.web_views import ExploreWebView, SearchWebView

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # Web Template Views
    path('', FeedWebView.as_view(), name='home'),
    path('feed/', FeedWebView.as_view(), name='feed'),
    path('explore/', ExploreWebView.as_view(), name='explore'),
    path('search/', SearchWebView.as_view(), name='search'),
    path('create/', PostCreateWebView.as_view(), name='post-create-direct'),
    path('auth/', include('apps.accounts.web_urls')),
    path('posts/', include('apps.posts.web_urls')),
    path('stories/', include('apps.stories.web_urls')),
    path('social/', include('apps.social.web_urls')),
    path('bookmarks/', include('apps.bookmarks.web_urls')),
    path('profile/', MyProfileRedirectWebView.as_view(), name='profile-me'),
    path('profile/edit/', ProfileEditWebView.as_view(), name='profile-edit'),
    path('@<str:identifier>/', ProfileWebView.as_view(), name='profile-view'),
    path('u/<str:identifier>/', ProfileWebView.as_view(), name='profile-view-alt'),

    # Direct Health Check (container / balancer probe)
    path('health/', HealthCheckAPIView.as_view(), name='health-check'),

    # API v1 Endpoints
    path('api/v1/', include([
        path('health/', HealthCheckAPIView.as_view(), name='api-health-check'),
        path('auth/', include('apps.accounts.urls')),
        path('profiles/', include('apps.profiles.urls')),
        path('posts/', include('apps.posts.urls')),
        path('feed/', FeedAPIView.as_view(), name='api-feed'),
        path('comments/', include('apps.comments.urls')),
        path('stories/', include('apps.stories.urls')),
        path('social/', include('apps.social.urls')),
        path('bookmarks/', include('apps.bookmarks.urls')),
        path('search/', include('apps.search.urls')),
        path('explore/', ExploreAPIView.as_view(), name='api-explore'),

        # OpenAPI 3 Schema & Interactive Documentation
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ])),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
