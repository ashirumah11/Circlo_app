import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.messaging.services import MessagingService

User = get_user_model()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email='alice@example.com',
        username='alice',
        password='Password123!',
        full_name='Alice Smith'
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email='bob@example.com',
        username='bob',
        password='Password123!',
        full_name='Bob Jones'
    )


@pytest.fixture
def user_c(db):
    return User.objects.create_user(
        email='carol@example.com',
        username='carol',
        password='Password123!',
        full_name='Carol Danvers'
    )


@pytest.mark.django_db
class TestMessagingWebViews:

    def test_inbox_web_view(self, user_a):
        client = Client()
        client.force_login(user_a)

        response = client.get('/messages/')
        assert response.status_code == 200
        assert 'inbox-container' in response.content.decode()

    def test_conversation_web_view_participant(self, user_a, user_b):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)
        client = Client()
        client.force_login(user_a)

        response = client.get(f'/messages/{conv.id}/')
        assert response.status_code == 200
        assert 'chat-view-container' in response.content.decode()
        assert 'bob' in response.content.decode()

    def test_conversation_web_view_non_participant_404(self, user_a, user_b, user_c):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)
        client = Client()
        client.force_login(user_c)

        response = client.get(f'/messages/{conv.id}/')
        assert response.status_code == 404

    def test_direct_message_user_redirect(self, user_a, user_b):
        client = Client()
        client.force_login(user_a)

        response = client.get(f'/messages/new/{user_b.username}/')
        assert response.status_code == 302
        assert '/messages/' in response.url
