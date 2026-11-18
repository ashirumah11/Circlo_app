import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Tests for REST API authentication endpoints."""

    def setup_method(self):
        self.client = APIClient()

    def test_registration_success(self):
        url = reverse('accounts:register')
        payload = {
            'email': 'maya@example.com',
            'username': 'maya_photo',
            'full_name': 'Maya Lin',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['username'] == 'maya_photo'
        assert response.data['user']['email'] == 'maya@example.com'
        assert 'circlo_refresh' in response.cookies

    def test_registration_duplicate_email(self):
        User.objects.create_user(
            email='existing@example.com',
            username='user_existing',
            full_name='Existing User',
            password='password123'
        )
        url = reverse('accounts:register')
        payload = {
            'email': 'existing@example.com',
            'username': 'brand_new',
            'full_name': 'Brand New',
            'password': 'password123',
            'password_confirm': 'password123',
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_registration_mismatched_passwords(self):
        url = reverse('accounts:register')
        payload = {
            'email': 'mismatch@example.com',
            'username': 'mismatch_user',
            'full_name': 'Mismatch User',
            'password': 'UniqueStrongPass2026!',
            'password_confirm': 'DifferentPass2026!',
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_login_with_email(self):
        User.objects.create_user(
            email='login.test@example.com',
            username='logintest',
            full_name='Login Test',
            password='SecretPassword123!'
        )
        url = reverse('accounts:login')
        payload = {
            'identifier': 'login.test@example.com',
            'password': 'SecretPassword123!'
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert response.data['user']['username'] == 'logintest'

    def test_login_with_username(self):
        User.objects.create_user(
            email='handle.test@example.com',
            username='handle_test',
            full_name='Handle Test',
            password='SecretPassword123!'
        )
        url = reverse('accounts:login')
        payload = {
            'identifier': 'handle_test',
            'password': 'SecretPassword123!'
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['email'] == 'handle.test@example.com'

    def test_login_invalid_credentials(self):
        url = reverse('accounts:login')
        payload = {
            'identifier': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_me_endpoint(self):
        user = User.objects.create_user(
            email='me@example.com',
            username='me_user',
            full_name='Me User',
            password='password123'
        )
        self.client.force_authenticate(user=user)
        url = reverse('accounts:me')

        # GET profile
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'me_user'

        # PATCH profile
        patch_payload = {
            'full_name': 'Updated Me',
            'bio': 'Coding with Django and Vite.',
            'location': 'Nairobi, Kenya',
            'is_private': True,
        }
        patch_resp = self.client.patch(url, patch_payload)
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.data['full_name'] == 'Updated Me'
        assert patch_resp.data['bio'] == 'Coding with Django and Vite.'
        assert patch_resp.data['is_private'] is True

    def test_change_password_api(self):
        user = User.objects.create_user(
            email='pwchange@example.com',
            username='pwchange',
            full_name='Pass Change',
            password='OldPassword123!'
        )
        self.client.force_authenticate(user=user)
        url = reverse('accounts:change-password')

        payload = {
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword456!',
            'new_password_confirm': 'NewPassword456!',
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('NewPassword456!') is True

    def test_logout_api(self):
        user = User.objects.create_user(
            email='logout@example.com',
            username='logout_user',
            full_name='Logout User',
            password='password123'
        )
        self.client.force_authenticate(user=user)
        url = reverse('accounts:logout')
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
