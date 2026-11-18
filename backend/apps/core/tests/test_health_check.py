import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheck:
    """
    Tests for health check endpoints.
    """

    def setup_method(self):
        self.client = APIClient()

    def test_direct_health_endpoint(self):
        url = reverse('health-check')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['status'] in ('healthy', 'degraded')
        assert 'version' in data
        assert 'timestamp' in data
        assert 'services' in data
        assert 'database' in data['services']
        assert data['services']['database']['status'] == 'healthy'

    def test_api_v1_health_endpoint(self):
        url = reverse('api-health-check')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['status'] in ('healthy', 'degraded')
        assert data['services']['database']['status'] == 'healthy'

    def test_home_page_renders_successfully(self):
        url = reverse('home')
        response = self.client.get(url)
        assert response.status_code == 200
        assert b'Welcome to Circlo' in response.content
