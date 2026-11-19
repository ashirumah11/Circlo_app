import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.notifications.services import NotificationService

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


@pytest.mark.django_db
class TestNotificationsWebViews:

    def test_notifications_web_view(self, user_a, user_b):
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='follow')

        client = Client()
        client.force_login(user_a)

        response = client.get('/notifications/')
        assert response.status_code == 200
        assert 'notifications-container' in response.content.decode()
        assert 'bob' in response.content.decode()

    def test_notifications_web_filter_unread(self, user_a, user_b):
        note = NotificationService.create_notification(recipient=user_a, actor=user_b, verb='follow')
        NotificationService.mark_as_read(note.id, user_a)

        client = Client()
        client.force_login(user_a)

        # Unread filter returns 0 items in list
        response = client.get('/notifications/?filter=unread')
        assert response.status_code == 200
        assert 'No notifications yet' in response.content.decode()

    def test_notifications_mark_all_read_action(self, user_a, user_b):
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='like_post')
        assert NotificationService.get_unread_count(user_a) == 1

        client = Client()
        client.force_login(user_a)

        response = client.post('/notifications/', {'action': 'mark_all_read'})
        assert response.status_code == 302
        assert NotificationService.get_unread_count(user_a) == 0
