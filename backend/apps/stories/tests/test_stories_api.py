from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.social.models import Follow
from apps.stories.models import Story, StoryView
from apps.stories.services import StoryService

User = get_user_model()


@pytest.mark.django_db
class TestStoriesAPI:
    """Tests for Stories REST API endpoints and business logic."""

    def setup_method(self):
        self.client = APIClient()
        self.author = User.objects.create_user(
            email='storyauthor@circlo.app',
            username='storyauthor',
            full_name='Story Author',
            password='StrongPass2026!'
        )
        self.viewer = User.objects.create_user(
            email='storyviewer@circlo.app',
            username='storyviewer',
            full_name='Story Viewer',
            password='StrongPass2026!'
        )
        self.dummy_img = SimpleUploadedFile(
            'story.jpg',
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9',
            'image/jpeg'
        )

    def test_upload_image_story(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('stories:stories-list-create')

        resp = self.client.post(url, {
            'file': self.dummy_img,
            'caption': 'Sunset story vibe!'
        }, format='multipart')

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['media_type'] == 'image'
        assert resp.data['caption'] == 'Sunset story vibe!'
        assert Story.objects.filter(author=self.author).exists()

    def test_story_feed_tray_groups_and_expiration(self):
        # Viewer follows author
        Follow.objects.create(follower=self.viewer, following=self.author, is_pending=False)

        # 1 active story
        active_story = StoryService.create_story(author=self.author, file=self.dummy_img, caption='Active story')

        # 1 expired story (created 25 hours ago)
        expired_story = StoryService.create_story(author=self.author, file=self.dummy_img, caption='Expired')
        expired_story.expires_at = timezone.now() - timedelta(hours=1)
        expired_story.save()

        # Query stories feed as viewer
        self.client.force_authenticate(user=self.viewer)
        url = reverse('stories:stories-list-create')
        resp = self.client.get(url)

        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1  # 1 author group
        group = resp.data[0]
        assert group['author']['username'] == 'storyauthor'
        assert len(group['stories']) == 1
        assert group['stories'][0]['id'] == active_story.id
        assert group['has_unviewed'] is True

    def test_record_story_view_and_viewers_list(self):
        story = StoryService.create_story(author=self.author, file=self.dummy_img)

        # 1. Viewer marks story as viewed
        self.client.force_authenticate(user=self.viewer)
        view_url = reverse('stories:story-record-view', kwargs={'pk': story.id})
        view_resp = self.client.post(view_url)

        assert view_resp.status_code == status.HTTP_200_OK
        assert view_resp.data['is_new_view'] is True
        assert view_resp.data['views_count'] == 1
        assert StoryView.objects.filter(story=story, viewer=self.viewer).exists()

        # 2. Duplicate view returns is_new_view=False without duplicate row
        view_resp2 = self.client.post(view_url)
        assert view_resp2.data['is_new_view'] is False
        assert StoryView.objects.filter(story=story).count() == 1

        # 3. Author checks viewers list
        self.client.force_authenticate(user=self.author)
        viewers_url = reverse('stories:story-viewers', kwargs={'pk': story.id})
        viewers_resp = self.client.get(viewers_url)
        assert viewers_resp.status_code == status.HTTP_200_OK
        assert len(viewers_resp.data['results']) == 1
        assert viewers_resp.data['results'][0]['viewer']['username'] == 'storyviewer'

        # 4. Non-author checking viewers list gets 403 Forbidden
        self.client.force_authenticate(user=self.viewer)
        forbidden_resp = self.client.get(viewers_url)
        assert forbidden_resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_story_permissions(self):
        story = StoryService.create_story(author=self.author, file=self.dummy_img)
        url = reverse('stories:story-detail', kwargs={'pk': story.id})

        # Non-author cannot delete
        self.client.force_authenticate(user=self.viewer)
        del_forbidden = self.client.delete(url)
        assert del_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert Story.objects.filter(id=story.id).exists()

        # Author can delete
        self.client.force_authenticate(user=self.author)
        del_resp = self.client.delete(url)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Story.objects.filter(id=story.id).exists()
