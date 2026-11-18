from django.urls import path
from .views import ExploreAPIView, UnifiedSearchAPIView

app_name = 'search'

urlpatterns = [
    path('', UnifiedSearchAPIView.as_view(), name='unified-search'),
    path('explore/', ExploreAPIView.as_view(), name='explore-posts'),
]
