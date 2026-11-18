import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from apps.posts.models import Post
from apps.posts.services import PostService

User = get_user_model()


@pytest.mark.django_db
class TestPostsWebViews:
    """Tests for server-rendered posts and feed pages."""

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='creator@circlo.app',
            username='creator',
            full_name='Content Creator',
            password='StrongPassword2026!'
        )
        self.dummy_img = SimpleUploadedFile(
            'photo.jpg',
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9',
            'image/jpeg'
        )

    def test_feed_view_authenticated_and_anonymous(self):
        # Anonymous viewing feed
        url = reverse('home')
        response = self.client.get(url)
        assert response.status_code == 200
        assert b'Welcome to Circlo Feed' in response.content or b'Following' in response.content

        # Create a post
        PostService.create_post(
            author=self.user,
            caption='A great shot of nature #wildlife',
            files=[self.dummy_img]
        )

        # Authenticated user viewing feed
        self.client.force_login(self.user)
        auth_resp = self.client.get(url)
        assert auth_resp.status_code == 200
        assert b'A great shot of nature #wildlife' in auth_resp.content

    def test_create_post_web(self):
        # Unauthenticated request to /create/ should redirect to login (not 404)
        anon_resp_shortcut = self.client.get('/create/')
        assert anon_resp_shortcut.status_code == 302
        assert '/auth/login/' in anon_resp_shortcut.url

        # Unauthenticated request to /posts/create/ should redirect to login (not 404)
        anon_resp = self.client.get('/posts/create/')
        assert anon_resp.status_code == 302
        assert '/auth/login/' in anon_resp.url

        # Authenticated user can access both routes
        self.client.force_login(self.user)
        create_url = reverse('post-create-web')

        shortcut_resp = self.client.get('/create/')
        assert shortcut_resp.status_code == 200
        assert b'Create new post' in shortcut_resp.content

        # GET creation form
        get_resp = self.client.get(create_url)
        assert get_resp.status_code == 200
        assert b'Create new post' in get_resp.content

        # POST create
        post_resp = self.client.post(create_url, {
            'caption': 'Shared from web interface #circlo',
            'location': 'New York, NY',
            'media': [self.dummy_img],
        }, follow=True)
        assert post_resp.status_code == 200
        assert Post.objects.filter(caption__contains='Shared from web interface').exists()

    def test_post_detail_and_comments_web(self):
        post = PostService.create_post(
            author=self.user,
            caption='Original Caption for Detail',
            files=[self.dummy_img]
        )
        detail_url = reverse('post-detail-web', kwargs={'pk': post.id})

        # GET detail page
        response = self.client.get(detail_url)
        assert response.status_code == 200
        assert b'Original Caption for Detail' in response.content

        # POST comment as authenticated user
        self.client.force_login(self.user)
        comment_url = reverse('post-comment-web', kwargs={'pk': post.id})
        comment_resp = self.client.post(comment_url, {'text': 'First web comment!'}, follow=True)
        assert comment_resp.status_code == 200
        assert b'First web comment!' in comment_resp.content

    def test_post_like_web_toggle(self):
        post = PostService.create_post(
            author=self.user,
            caption='Test like web',
            files=[self.dummy_img]
        )
        self.client.force_login(self.user)
        like_url = reverse('post-like-web', kwargs={'pk': post.id})

        # POST like (simulating standard form submit)
        resp = self.client.post(like_url, {'next': f'/posts/{post.id}/'}, follow=True)
        assert resp.status_code == 200
        assert post.likes.count() == 1

        # POST like again (unlike)
        resp2 = self.client.post(like_url, {'next': f'/posts/{post.id}/'}, follow=True)
        assert resp2.status_code == 200
        assert post.likes.count() == 0
