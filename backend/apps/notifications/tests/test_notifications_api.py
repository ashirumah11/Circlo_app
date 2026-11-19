import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.comments.services import CommentService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.posts.models import Post
from apps.posts.services import PostService
from apps.social.services import SocialService

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
class TestNotificationServiceAndAPI:

    def test_direct_notification_creation(self, user_a, user_b):
        note = NotificationService.create_notification(
            recipient=user_a,
            actor=user_b,
            verb='follow',
            text='started following you.'
        )
        assert note is not None
        assert note.recipient == user_a
        assert note.actor == user_b
        assert note.is_read is False

    def test_self_notification_prevented(self, user_a):
        note = NotificationService.create_notification(
            recipient=user_a,
            actor=user_a,
            verb='like_post',
            text='liked own post'
        )
        assert note is None
        assert Notification.objects.count() == 0

    def test_post_like_triggers_notification(self, user_a, user_b):
        post = Post.objects.create(author=user_a, caption="Exciting photo!")
        # Bob likes Alice's post
        PostService.toggle_like(post=post, user=user_b)

        note = Notification.objects.filter(recipient=user_a, actor=user_b, verb='like_post').first()
        assert note is not None
        assert note.target_id == post.id

    def test_comment_triggers_notification(self, user_a, user_b):
        post = Post.objects.create(author=user_a, caption="Photo post")
        # Bob comments on Alice's post
        CommentService.create_comment(post=post, user=user_b, text="Great photo!")

        note = Notification.objects.filter(recipient=user_a, actor=user_b, verb='comment').first()
        assert note is not None
        assert "Great photo!" in note.text

    def test_follow_triggers_notification(self, user_a, user_b):
        # Bob follows Alice
        SocialService.toggle_follow(follower=user_b, target_user=user_a)

        note = Notification.objects.filter(recipient=user_a, actor=user_b, verb='follow').first()
        assert note is not None

    def test_list_notifications_and_unread_filter(self, api_client_a, user_a, user_b):
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='follow')
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='like_post')

        # List all
        resp = api_client_a.get('/api/v1/notifications/')
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()['results']) == 2

        # Mark one as read
        first_id = resp.json()['results'][0]['id']
        NotificationService.mark_as_read(first_id, user_a)

        # Filter unread
        unread_resp = api_client_a.get('/api/v1/notifications/?unread=true')
        assert unread_resp.status_code == status.HTTP_200_OK
        assert len(unread_resp.json()['results']) == 1

    def test_mark_all_read_api(self, api_client_a, user_a, user_b):
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='follow')
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='comment')

        assert NotificationService.get_unread_count(user_a) == 2

        resp = api_client_a.post('/api/v1/notifications/read-all/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['updated_count'] == 2
        assert NotificationService.get_unread_count(user_a) == 0

    def test_unread_count_api(self, api_client_a, user_a, user_b):
        NotificationService.create_notification(recipient=user_a, actor=user_b, verb='follow')
        resp = api_client_a.get('/api/v1/notifications/unread-count/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['unread_count'] == 1
