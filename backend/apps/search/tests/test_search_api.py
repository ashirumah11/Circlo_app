import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.services import PostService

User = get_user_model()


@pytest.mark.django_db
class TestSearchAPI:
    """Tests for unified search and explore discovery feed."""

    def setup_method(self):
        self.client = APIClient()
        self.user_photographer = User.objects.create_user(
            email='photo@circlo.app',
            username='photographer_dan',
            full_name='Dan Photographer',
            password='Password123!'
        )
        dummy_img = SimpleUploadedFile('shot.jpg', b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9', 'image/jpeg')
        self.post = PostService.create_post(
            author=self.user_photographer,
            caption='Golden sunset in Santorini #greece #sunset',
            files=[dummy_img],
            location='Santorini, Greece'
        )

    def test_search_users_by_query(self):
        url = reverse('search:unified-search') + '?q=dan&type=users'
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['users']) >= 1
        assert resp.data['users'][0]['username'] == 'photographer_dan'

    def test_search_hashtags_by_query(self):
        url = reverse('search:unified-search') + '?q=sunset&type=hashtags'
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['hashtags']) >= 1
        assert resp.data['hashtags'][0]['name'] == 'sunset'

    def test_search_posts_by_caption(self):
        url = reverse('search:unified-search') + '?q=Santorini&type=posts'
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['posts']) >= 1
        assert 'Santorini' in resp.data['posts'][0]['caption']

    def test_unified_search_returns_all_categories(self):
        url = reverse('search:unified-search') + '?q=sunset'
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert 'users' in resp.data
        assert 'hashtags' in resp.data
        assert 'posts' in resp.data

    def test_explore_feed_endpoint(self):
        url = reverse('search:explore-posts')
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 1
        assert resp.data[0]['id'] == self.post.id
