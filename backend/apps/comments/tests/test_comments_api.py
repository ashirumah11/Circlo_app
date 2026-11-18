import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.comments.models import Comment
from apps.posts.services import PostService

User = get_user_model()


@pytest.mark.django_db
class TestCommentsAPI:
    """Tests for Comments and threaded replies REST API endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='commenter@circlo.app',
            username='commenter',
            full_name='Commenter User',
            password='StrongPass2026!'
        )
        self.author = User.objects.create_user(
            email='poster@circlo.app',
            username='poster',
            full_name='Post Author',
            password='StrongPass2026!'
        )
        dummy_img = SimpleUploadedFile('img.png', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82', 'image/png')
        self.post = PostService.create_post(
            author=self.author,
            caption='Post with comments',
            files=[dummy_img]
        )

    def test_create_comment_on_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:post-comments', kwargs={'pk': self.post.id})

        payload = {'text': 'Amazing composition and colors!'}
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['text'] == 'Amazing composition and colors!'
        assert response.data['user']['username'] == 'commenter'
        assert response.data['parent_id'] is None
        assert response.data['likes_count'] == 0

    def test_create_threaded_reply_on_comment(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:post-comments', kwargs={'pk': self.post.id})

        # Top-level comment
        resp1 = self.client.post(url, {'text': 'Where was this taken?'})
        parent_id = resp1.data['id']

        # Reply from post author
        self.client.force_authenticate(user=self.author)
        resp_reply = self.client.post(url, {
            'text': 'This was taken in Big Sur, California!',
            'parent_id': parent_id
        })
        assert resp_reply.status_code == status.HTTP_201_CREATED
        assert resp_reply.data['parent_id'] == parent_id

        # Listing comments returns nested replies
        get_resp = self.client.get(url)
        assert get_resp.status_code == status.HTTP_200_OK
        assert len(get_resp.data) == 1
        assert len(get_resp.data[0]['replies']) == 1
        assert get_resp.data[0]['replies'][0]['text'] == 'This was taken in Big Sur, California!'

    def test_comment_like_toggle(self):
        self.client.force_authenticate(user=self.user)
        post_comments_url = reverse('posts:post-comments', kwargs={'pk': self.post.id})
        create_resp = self.client.post(post_comments_url, {'text': 'Awesome!'})
        comment_id = create_resp.data['id']

        like_url = reverse('comments:comment-like-toggle', kwargs={'pk': comment_id})

        # Like comment
        like_resp = self.client.post(like_url)
        assert like_resp.status_code == status.HTTP_200_OK
        assert like_resp.data['is_liked'] is True
        assert like_resp.data['likes_count'] == 1

        # Unlike comment
        unlike_resp = self.client.post(like_url)
        assert unlike_resp.status_code == status.HTTP_200_OK
        assert unlike_resp.data['is_liked'] is False
        assert unlike_resp.data['likes_count'] == 0

    def test_comment_delete_permissions(self):
        self.client.force_authenticate(user=self.user)
        post_comments_url = reverse('posts:post-comments', kwargs={'pk': self.post.id})
        create_resp = self.client.post(post_comments_url, {'text': 'Temporary comment'})
        comment_id = create_resp.data['id']

        detail_url = reverse('comments:comment-detail', kwargs={'pk': comment_id})

        # Another user cannot delete
        other = User.objects.create_user(email='other@circlo.app', username='other', full_name='Other', password='Password123!')
        self.client.force_authenticate(user=other)
        assert self.client.delete(detail_url).status_code == status.HTTP_403_FORBIDDEN

        # Comment author can delete
        self.client.force_authenticate(user=self.user)
        assert self.client.delete(detail_url).status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(pk=comment_id).exists()
