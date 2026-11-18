import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.social.models import Block, Follow
from apps.social.services import SocialService

User = get_user_model()


@pytest.mark.django_db
class TestSocialGraphAPI:
    """Tests for Social relationships: follow, unfollow, private requests, and blocking."""

    def setup_method(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email='alice@circlo.app',
            username='alice',
            full_name='Alice Wonderland',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='bob@circlo.app',
            username='bob',
            full_name='Bob Builder',
            password='Password123!',
            is_private=False
        )
        self.user_private = User.objects.create_user(
            email='charlie@circlo.app',
            username='charlie',
            full_name='Charlie Private',
            password='Password123!',
            is_private=True
        )

    def test_follow_public_user_toggle(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('profiles:profile-follow-toggle', kwargs={'id': self.user_b.id})

        # 1. Follow public user
        resp = self.client.post(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['is_following'] is True
        assert resp.data['is_pending'] is False
        assert Follow.objects.filter(follower=self.user_a, following=self.user_b, is_pending=False).exists()

        # 2. Toggle again to unfollow
        resp_unfollow = self.client.post(url)
        assert resp_unfollow.status_code == status.HTTP_200_OK
        assert resp_unfollow.data['is_following'] is False
        assert not Follow.objects.filter(follower=self.user_a, following=self.user_b).exists()

    def test_follow_private_user_creates_pending_request(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('profiles:profile-follow-toggle', kwargs={'id': self.user_private.id})

        resp = self.client.post(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['is_following'] is False
        assert resp.data['is_pending'] is True
        assert resp.data['status'] == 'requested'

        follow_req = Follow.objects.filter(follower=self.user_a, following=self.user_private, is_pending=True).first()
        assert follow_req is not None

        # Charlie checks pending requests
        self.client.force_authenticate(user=self.user_private)
        requests_url = reverse('social:pending-requests')
        req_resp = self.client.get(requests_url)
        assert req_resp.status_code == status.HTTP_200_OK
        assert len(req_resp.data['results']) == 1
        assert req_resp.data['results'][0]['follower']['username'] == 'alice'

        # Charlie accepts request
        accept_url = reverse('social:accept-request', kwargs={'pk': follow_req.id})
        accept_resp = self.client.post(accept_url)
        assert accept_resp.status_code == status.HTTP_200_OK
        follow_req.refresh_from_db()
        assert follow_req.is_pending is False

    def test_reject_follow_request(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('profiles:profile-follow-toggle', kwargs={'id': self.user_private.id})
        self.client.post(url)

        follow_req = Follow.objects.get(follower=self.user_a, following=self.user_private, is_pending=True)

        # Charlie rejects
        self.client.force_authenticate(user=self.user_private)
        reject_url = reverse('social:reject-request', kwargs={'pk': follow_req.id})
        reject_resp = self.client.post(reject_url)
        assert reject_resp.status_code == status.HTTP_200_OK
        assert not Follow.objects.filter(id=follow_req.id).exists()

    def test_self_follow_forbidden(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('profiles:profile-follow-toggle', kwargs={'id': self.user_a.id})
        resp = self.client.post(url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_block_user_toggle_and_severs_follows(self):
        # Alice follows Bob
        Follow.objects.create(follower=self.user_a, following=self.user_b, is_pending=False)
        Follow.objects.create(follower=self.user_b, following=self.user_a, is_pending=False)

        self.client.force_authenticate(user=self.user_a)
        block_url = reverse('profiles:profile-block-toggle', kwargs={'id': self.user_b.id})

        # Block Bob
        block_resp = self.client.post(block_url)
        assert block_resp.status_code == status.HTTP_200_OK
        assert block_resp.data['is_blocked'] is True

        # Follow connection should be wiped in both directions
        assert not Follow.objects.filter(follower=self.user_a, following=self.user_b).exists()
        assert not Follow.objects.filter(follower=self.user_b, following=self.user_a).exists()
        assert Block.objects.filter(blocker=self.user_a, blocked=self.user_b).exists()

        # Unblock Bob
        unblock_resp = self.client.post(block_url)
        assert unblock_resp.status_code == status.HTTP_200_OK
        assert unblock_resp.data['is_blocked'] is False
        assert not Block.objects.filter(blocker=self.user_a, blocked=self.user_b).exists()
