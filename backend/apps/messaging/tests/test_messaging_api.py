import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.messaging.models import Conversation, Message
from apps.messaging.services import MessagingService
from apps.social.models import Block

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


@pytest.fixture
def api_client_a(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def api_client_b(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


@pytest.mark.django_db
class TestMessagingServiceAndAPI:

    def test_start_conversation_success(self, api_client_a, user_a, user_b):
        response = api_client_a.post('/api/v1/conversations/', {
            'recipient_id': user_b.id
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] is not None
        assert len(data['participants']) == 2

    def test_cannot_start_conversation_with_self(self, api_client_a, user_a):
        response = api_client_a.post('/api/v1/conversations/', {
            'recipient_id': user_a.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_start_conversation_if_blocked(self, api_client_a, user_a, user_b):
        Block.objects.create(blocker=user_b, blocked=user_a)
        response = api_client_a.post('/api/v1/conversations/', {
            'recipient_id': user_b.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_and_list_messages(self, api_client_a, api_client_b, user_a, user_b):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)

        # Alice sends a message
        send_resp = api_client_a.post(f'/api/v1/conversations/{conv.id}/messages/', {
            'text': 'Hello Bob!'
        })
        assert send_resp.status_code == status.HTTP_201_CREATED
        msg_id = send_resp.json()['id']

        # Bob reads messages
        list_resp = api_client_b.get(f'/api/v1/conversations/{conv.id}/messages/')
        assert list_resp.status_code == status.HTTP_200_OK
        messages = list_resp.json()
        assert len(messages) == 1
        assert messages[0]['id'] == msg_id
        assert messages[0]['text'] == 'Hello Bob!'
        assert messages[0]['is_read'] is False

    def test_mark_conversation_as_read(self, api_client_a, api_client_b, user_a, user_b):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)
        MessagingService.send_message(conv, sender=user_a, text='Unread message')

        # Bob has 1 unread message
        assert conv.get_unread_count(user_b) == 1

        # Bob marks conversation as read
        read_resp = api_client_b.post(f'/api/v1/conversations/{conv.id}/read/')
        assert read_resp.status_code == status.HTTP_200_OK
        assert read_resp.json()['updated_count'] == 1

        # Now Bob has 0 unread messages
        assert conv.get_unread_count(user_b) == 0

    def test_unread_count_api(self, api_client_b, user_a, user_b):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)
        MessagingService.send_message(conv, sender=user_a, text='Message 1')
        MessagingService.send_message(conv, sender=user_a, text='Message 2')

        resp = api_client_b.get('/api/v1/conversations/unread-count/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['unread_count'] == 2

    def test_non_participant_forbidden(self, user_a, user_b, user_c):
        conv = MessagingService.get_or_create_conversation(user_a, user_b)
        client_c = APIClient()
        client_c.force_authenticate(user=user_c)

        # Carol cannot read messages between Alice and Bob
        resp = client_c.get(f'/api/v1/conversations/{conv.id}/messages/')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Carol cannot send messages to this conversation
        post_resp = client_c.post(f'/api/v1/conversations/{conv.id}/messages/', {'text': 'Intruder'})
        assert post_resp.status_code == status.HTTP_403_FORBIDDEN
