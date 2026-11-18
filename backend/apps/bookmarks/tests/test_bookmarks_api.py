import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookmarks.models import Bookmark
from apps.posts.services import PostService

User = get_user_model()


@pytest.mark.django_db
class TestBookmarksAPI:
    """Tests for post saving and bookmarks API."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='saver@circlo.app',
            username='saver',
            full_name='Post Saver',
            password='StrongPass2026!'
        )
        self.author = User.objects.create_user(
            email='author@circlo.app',
            username='author',
            full_name='Post Author',
            password='StrongPass2026!'
        )
        dummy_img = SimpleUploadedFile('save.jpg', b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9', 'image/jpeg')
        self.post = PostService.create_post(
            author=self.author,
            caption='A memorable post to bookmark #inspiration',
            files=[dummy_img]
        )

    def test_toggle_bookmark_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:post-bookmark-toggle', kwargs={'pk': self.post.id})

        # Save post
        resp = self.client.post(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['is_bookmarked'] is True
        assert Bookmark.objects.filter(user=self.user, post=self.post).exists()

        # Check in user bookmarks list
        list_url = reverse('bookmarks:bookmark-list')
        list_resp = self.client.get(list_url)
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.data['results']) == 1
        assert list_resp.data['results'][0]['id'] == self.post.id

        # Toggle to remove from bookmarks
        resp_remove = self.client.post(url)
        assert resp_remove.status_code == status.HTTP_200_OK
        assert resp_remove.data['is_bookmarked'] is False
        assert not Bookmark.objects.filter(user=self.user, post=self.post).exists()
