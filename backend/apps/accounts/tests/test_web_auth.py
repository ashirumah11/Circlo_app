import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestWebAuthViews:
    """Tests for server-rendered HTML views and session handling."""

    def setup_method(self):
        self.client = Client()

    def test_register_get_and_post(self):
        url = reverse('accounts-web:register')
        get_resp = self.client.get(url)
        assert get_resp.status_code == 200
        assert b'Create your Circlo account' in get_resp.content

        # POST register
        payload = {
            'email': 'webuser@example.com',
            'username': 'webuser',
            'full_name': 'Web User',
            'password': 'StrongWebPassword123!',
            'password_confirm': 'StrongWebPassword123!',
        }
        post_resp = self.client.post(url, payload, follow=True)
        assert post_resp.status_code == 200
        # User is logged in to session and redirected to home
        user = User.objects.get(username='webuser')
        assert user is not None

    def test_login_and_logout_web(self):
        User.objects.create_user(
            email='member@circlo.app',
            username='circlo_member',
            full_name='Circlo Member',
            password='MemberPassword123!'
        )
        login_url = reverse('accounts-web:login')

        # Login with username
        post_resp = self.client.post(login_url, {
            'identifier': 'circlo_member',
            'password': 'MemberPassword123!'
        }, follow=True)
        assert post_resp.status_code == 200
        assert b'Welcome back' in post_resp.content

        # Logout
        logout_url = reverse('accounts-web:logout')
        logout_resp = self.client.get(logout_url, follow=True)
        assert logout_resp.status_code == 200
        assert b'You have been logged out.' in logout_resp.content

    def test_profile_web_view(self):
        user = User.objects.create_user(
            email='profiletest@circlo.app',
            username='artist',
            full_name='Creative Artist',
            password='password123',
            bio='Photography and Architecture'
        )
        url = reverse('profile-view', kwargs={'identifier': 'artist'})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b'Creative Artist' in response.content
        assert b'Photography and Architecture' in response.content
        assert b'Follow' in response.content

    def test_profile_edit_web_view(self):
        user = User.objects.create_user(
            email='editor@circlo.app',
            username='editor_user',
            full_name='Original Name',
            password='password123'
        )
        self.client.force_login(user)

        edit_url = reverse('profile-edit')
        get_resp = self.client.get(edit_url)
        assert get_resp.status_code == 200
        assert b'Edit Profile' in get_resp.content

        # POST updates
        payload = {
            'full_name': 'Brand New Name',
            'bio': 'Updated bio through web form.',
            'website': 'https://portfolio.example.com',
            'location': 'Tokyo, Japan',
            'is_private': 'on',
        }
        post_resp = self.client.post(edit_url, payload, follow=True)
        assert post_resp.status_code == 200

        user.refresh_from_db()
        assert user.full_name == 'Brand New Name'
        assert user.bio == 'Updated bio through web form.'
        assert user.is_private is True
