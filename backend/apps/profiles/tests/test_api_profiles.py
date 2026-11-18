import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestProfilesAPI:
    """Tests for Profile REST API endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@circlo.app',
            username='user_one',
            full_name='User One',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='user2@circlo.app',
            username='user_two',
            full_name='User Two',
            password='password123'
        )

    def test_list_and_search_profiles(self):
        url = reverse('profiles:profile-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

        # Search by username
        search_resp = self.client.get(f"{url}?search=user_one")
        assert search_resp.status_code == status.HTTP_200_OK
        assert search_resp.data['count'] == 1
        assert search_resp.data['results'][0]['username'] == 'user_one'

    def test_get_profile_by_id_and_by_handle(self):
        # By ID
        url_id = reverse('profiles:profile-detail', kwargs={'id': self.user1.id})
        resp_id = self.client.get(url_id)
        assert resp_id.status_code == status.HTTP_200_OK
        assert resp_id.data['username'] == 'user_one'

        # By @handle
        url_handle = reverse('profiles:profile-detail', kwargs={'id': '@user_two'})
        resp_handle = self.client.get(url_handle)
        assert resp_handle.status_code == status.HTTP_200_OK
        assert resp_handle.data['username'] == 'user_two'

    def test_update_profile_owner_permitted(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('profiles:profile-detail', kwargs={'id': self.user1.id})
        payload = {'bio': 'Updated bio via API.'}
        response = self.client.patch(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Updated bio via API.'

    def test_update_profile_forbidden_for_other_users(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('profiles:profile-detail', kwargs={'id': self.user2.id})
        payload = {'bio': 'Hacked bio!'}
        response = self.client.patch(url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
