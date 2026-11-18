import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Hashtag, Post

User = get_user_model()


@pytest.mark.django_db
class TestPostsAPI:
    """Tests for Posts REST API endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.author = User.objects.create_user(
            email='photographer@circlo.app',
            username='photographer',
            full_name='Pro Photographer',
            password='StrongPass2026!'
        )
        self.other_user = User.objects.create_user(
            email='viewer@circlo.app',
            username='viewer_user',
            full_name='Viewer User',
            password='StrongPass2026!'
        )
        # Dummy small image bytes (1x1 transparent PNG)
        self.dummy_image = SimpleUploadedFile(
            name='test_photo.png',
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )

    def test_create_post_success_with_media_and_hashtags(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('posts:post-list-create')

        payload = {
            'caption': 'Sunset over the bay #ocean #photography #goldenhour',
            'location': 'San Francisco, CA',
            'media': [self.dummy_image],
        }
        response = self.client.post(url, payload, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['author']['username'] == 'photographer'
        assert response.data['caption'] == 'Sunset over the bay #ocean #photography #goldenhour'
        assert len(response.data['media']) == 1
        assert response.data['likes_count'] == 0
        assert response.data['comments_count'] == 0

        # Verify hashtags extraction
        post = Post.objects.get(pk=response.data['id'])
        assert post.hashtags.count() == 3
        assert set(post.hashtags.values_list('name', flat=True)) == {'ocean', 'photography', 'goldenhour'}

    def test_create_post_missing_media_fails(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('posts:post-list-create')
        payload = {'caption': 'Text-only post should fail!'}
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_post_unsupported_file_type_fails(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('posts:post-list-create')
        invalid_file = SimpleUploadedFile(
            name='script.exe',
            content=b'binary data',
            content_type='application/x-msdownload'
        )
        payload = {'caption': 'Test', 'media': [invalid_file]}
        response = self.client.post(url, payload, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_posts_list_and_filters(self):
        self.client.force_authenticate(user=self.author)
        # Create a post
        post_url = reverse('posts:post-list-create')
        self.client.post(post_url, {
            'caption': 'Hello world #circlo',
            'media': [self.dummy_image],
        }, format='multipart')

        # List all
        response = self.client.get(post_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

        # Filter by author
        resp_author = self.client.get(f"{post_url}?author=photographer")
        assert resp_author.status_code == status.HTTP_200_OK
        assert resp_author.data['count'] >= 1

        # Filter by hashtag
        resp_tag = self.client.get(f"{post_url}?hashtag=circlo")
        assert resp_tag.status_code == status.HTTP_200_OK
        assert resp_tag.data['count'] >= 1

    def test_post_detail_update_delete(self):
        self.client.force_authenticate(user=self.author)
        create_resp = self.client.post(reverse('posts:post-list-create'), {
            'caption': 'Initial caption',
            'media': [self.dummy_image],
        }, format='multipart')
        post_id = create_resp.data['id']

        detail_url = reverse('posts:post-detail', kwargs={'pk': post_id})

        # GET detail
        get_resp = self.client.get(detail_url)
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.data['caption'] == 'Initial caption'

        # PATCH update by author
        patch_resp = self.client.patch(detail_url, {'caption': 'Updated caption #fresh'})
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.data['caption'] == 'Updated caption #fresh'

        # PATCH update by other user is forbidden
        self.client.force_authenticate(user=self.other_user)
        forbidden_resp = self.client.patch(detail_url, {'caption': 'Unauthorized edit'})
        assert forbidden_resp.status_code == status.HTTP_403_FORBIDDEN

        # DELETE by other user is forbidden
        del_forbidden = self.client.delete(detail_url)
        assert del_forbidden.status_code == status.HTTP_403_FORBIDDEN

        # DELETE by author
        self.client.force_authenticate(user=self.author)
        del_resp = self.client.delete(detail_url)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(pk=post_id).exists()

    def test_post_like_toggle(self):
        self.client.force_authenticate(user=self.author)
        create_resp = self.client.post(reverse('posts:post-list-create'), {
            'caption': 'Like this photo!',
            'media': [self.dummy_image],
        }, format='multipart')
        post_id = create_resp.data['id']

        like_url = reverse('posts:post-like-toggle', kwargs={'pk': post_id})

        # Like
        like_resp = self.client.post(like_url)
        assert like_resp.status_code == status.HTTP_200_OK
        assert like_resp.data['is_liked'] is True
        assert like_resp.data['likes_count'] == 1

        # Unlike
        unlike_resp = self.client.post(like_url)
        assert unlike_resp.status_code == status.HTTP_200_OK
        assert unlike_resp.data['is_liked'] is False
        assert unlike_resp.data['likes_count'] == 0
