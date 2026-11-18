import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.social.models import Follow

User = get_user_model()


@pytest.mark.django_db
class TestSocialWebViews:
    """Tests for Phase 4 server-rendered social, explore, search and saved web pages."""

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='webuser@circlo.app',
            username='webuser',
            full_name='Web User',
            password='Password123!'
        )
        self.target = User.objects.create_user(
            email='target@circlo.app',
            username='target',
            full_name='Target User',
            password='Password123!'
        )

    def test_explore_web_view(self):
        resp = self.client.get(reverse('explore'))
        assert resp.status_code == 200
        assert b'Discover Circlo' in resp.content or b'explore-grid' in resp.content

    def test_search_web_view(self):
        resp = self.client.get(reverse('search') + '?q=target')
        assert resp.status_code == 200
        assert b'target' in resp.content

    def test_follow_toggle_web(self):
        self.client.force_login(self.user)
        follow_url = reverse('social-web:follow-toggle', kwargs={'pk': self.target.id})

        # POST follow
        resp = self.client.post(follow_url, {'next': f'/@{self.target.username}/'}, follow=True)
        assert resp.status_code == 200
        assert Follow.objects.filter(follower=self.user, following=self.target, is_pending=False).exists()

        # POST unfollow
        resp_unfollow = self.client.post(follow_url, {'next': f'/@{self.target.username}/'}, follow=True)
        assert resp_unfollow.status_code == 200
        assert not Follow.objects.filter(follower=self.user, following=self.target).exists()

    def test_saved_posts_web_view(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('bookmarks-web:saved-posts'))
        assert resp.status_code == 200
        assert b'Saved Posts' in resp.content
