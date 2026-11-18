import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """
    Tests for the custom User model and UserManager.
    """

    def test_create_user_successful(self):
        user = User.objects.create_user(
            email='alice@example.com',
            username='alice_dev',
            full_name='Alice Wonderland',
            password='strong-password-123'
        )
        assert user.pk is not None
        assert user.email == 'alice@example.com'
        assert user.username == 'alice_dev'
        assert user.full_name == 'Alice Wonderland'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_private is False
        assert user.check_password('strong-password-123') is True
        assert str(user) == '@alice_dev (alice@example.com)'
        assert user.avatar_url == '/static/images/default-avatar.svg'

    def test_email_and_username_normalization(self):
        user = User.objects.create_user(
            email='Bob.Smith@EXAMPLE.COM',
            username='BobSmith',
            full_name='Bob Smith',
            password='password123'
        )
        assert user.email == 'bob.smith@example.com'
        assert user.username == 'bobsmith'

    def test_create_user_missing_email_raises_error(self):
        with pytest.raises(ValueError, match='The Email field is required.'):
            User.objects.create_user(
                email='',
                username='nouser',
                full_name='No User',
                password='password123'
            )

    def test_create_user_missing_username_raises_error(self):
        with pytest.raises(ValueError, match='The Username field is required.'):
            User.objects.create_user(
                email='test@example.com',
                username='',
                full_name='No Username',
                password='password123'
            )

    def test_create_superuser_successful(self):
        admin = User.objects.create_superuser(
            email='admin@circlo.app',
            username='admin',
            full_name='Admin User',
            password='admin-secure-password'
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.is_email_verified is True
        assert admin.is_active is True

    def test_unique_email_constraint(self):
        User.objects.create_user(
            email='duplicate@example.com',
            username='user_one',
            full_name='User One',
            password='password123'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='duplicate@example.com',
                username='user_two',
                full_name='User Two',
                password='password123'
            )

    def test_unique_username_constraint(self):
        User.objects.create_user(
            email='one@example.com',
            username='same_handle',
            full_name='User One',
            password='password123'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='two@example.com',
                username='same_handle',
                full_name='User Two',
                password='password123'
            )

    def test_authenticate_with_email_or_username(self):
        User.objects.create_user(
            email='claire@example.com',
            username='claire99',
            full_name='Claire Redfield',
            password='secret-claire-pass'
        )

        # Authenticate using email
        user_by_email = authenticate(
            username='claire@example.com',
            password='secret-claire-pass'
        )
        assert user_by_email is not None
        assert user_by_email.username == 'claire99'

        # Authenticate using username
        user_by_username = authenticate(
            username='claire99',
            password='secret-claire-pass'
        )
        assert user_by_username is not None
        assert user_by_username.email == 'claire@example.com'

        # Invalid password returns None
        assert authenticate(username='claire99', password='wrong-password') is None
