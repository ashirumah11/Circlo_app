import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestApiDocumentation:
    """
    Tests for drf-spectacular OpenAPI schema and Swagger UI endpoints.
    """

    def setup_method(self):
        self.client = APIClient()

    def test_openapi_schema_endpoint(self):
        url = reverse('schema')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Schema should contain OpenAPI definition
        assert 'openapi' in response.data or 'paths' in response.data or 'info' in response.data
        assert response.data['info']['title'] == 'Circlo Social Media API'
        assert response.data['info']['version'] == '1.0.0'

    def test_swagger_ui_endpoint(self):
        url = reverse('swagger-ui')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert b'swagger-ui' in response.content.lower()

    def test_redoc_endpoint(self):
        url = reverse('redoc')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert b'redoc' in response.content.lower()
