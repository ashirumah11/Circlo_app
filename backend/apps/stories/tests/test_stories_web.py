import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from apps.stories.models import Story
from apps.stories.services import StoryService

User = get_user_model()


@pytest.mark.django_db
class TestStoriesWebViews:
    """Tests for Phase 5 server-rendered story creation and viewer pages."""

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='storyweb@circlo.app',
            username='storywebuser',
            full_name='Story Web User',
            password='Password123!'
        )
        self.dummy_img = SimpleUploadedFile(
            'story_web.jpg',
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9',
            'image/jpeg'
        )

    def test_story_create_web_unauthenticated_redirect(self):
        url = reverse('stories-web:story-create')
        resp = self.client.get(url)
        assert resp.status_code == 302
        assert '/auth/login/' in resp.url

    def test_story_create_web_authenticated(self):
        self.client.force_login(self.user)
        url = reverse('stories-web:story-create')

        # GET form
        get_resp = self.client.get(url)
        assert get_resp.status_code == 200
        assert b'Share a Story' in get_resp.content

        # POST story
        post_resp = self.client.post(url, {
            'media': self.dummy_img,
            'caption': 'Shared from web story UI'
        }, follow=True)
        assert post_resp.status_code == 200
        assert Story.objects.filter(author=self.user, caption='Shared from web story UI').exists()

    def test_story_viewer_web(self):
        StoryService.create_story(
            author=self.user,
            file=self.dummy_img,
            caption='Story in Viewer'
        )

        viewer_url = reverse('stories-web:story-viewer', kwargs={'username': self.user.username})
        resp = self.client.get(viewer_url)
        assert resp.status_code == 200
        assert b'story-card' in resp.content
        assert b'storywebuser' in resp.content
