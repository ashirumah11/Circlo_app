from django.urls import path
from .views import HealthCheckAPIView, HomeView

urlpatterns = [
    path('health/', HealthCheckAPIView.as_view(), name='api-health-check'),
]
