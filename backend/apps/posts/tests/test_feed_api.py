import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.services import PostService

User = get_user_model()


@pytest.mark.django_db
class TestFeedAPI:
    """Tests for Feed REST API endpoint."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='feeduser@circlo.app',
            username='feeduser',
            full_name='Feed User',
            password='Password2026!'
        )
        dummy_img = SimpleUploadedFile('img.png', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82', 'image/png')
        self.post1 = PostService.create_post(self.user, 'First Post #one', [dummy_img])
        self.post2 = PostService.create_post(self.user, 'Second Post #two', [dummy_img])

    def test_get_feed_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api-feed')

        # Following filter
        response = self.client.get(f"{url}?filter=following")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['caption'] == 'Second Post #two'

        # Latest filter
        response_latest = self.client.get(f"{url}?filter=latest")
        assert response_latest.status_code == status.HTTP_200_OK
        assert response_latest.data['count'] == 2

    def test_get_feed_anonymous(self):
        url = reverse('api-feed')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
