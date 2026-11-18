import json
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Story
from .services import StoryService

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class StoryCreateWebView(View):
    """
    Renders the story upload page and processes new story uploads.
    """
    template_name = 'stories/create.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        file = request.FILES.get('media')
        caption = request.POST.get('caption', '')

        if not file:
            messages.error(request, 'Please select an image or video file to share.')
            return render(request, self.template_name, {'caption': caption})

        try:
            story = StoryService.create_story(
                author=request.user,
                file=file,
                caption=caption
            )
            messages.success(request, 'Your story has been shared!')
            return redirect('feed')
        except Exception as e:
            messages.error(request, str(e))
            return render(request, self.template_name, {'caption': caption})


class StoryViewerWebView(View):
    """
    Renders the interactive full-screen story viewer.
    Can be loaded by author username: /stories/@<username>/
    """
    template_name = 'stories/viewer.html'

    def get(self, request, username):
        clean_username = username.lstrip('@')
        author = get_object_or_404(User, username=clean_username, is_active=True)

        groups = StoryService.get_active_stories_grouped(viewer=request.user)
        author_group = next((g for g in groups if g['author'].id == author.id), None)

        if not author_group or not author_group['stories']:
            messages.info(request, f"No active stories available for @{author.username}.")
            return redirect('feed')

        # Automatically record view on first story if viewer is authenticated
        if request.user.is_authenticated and author_group['stories']:
            StoryService.record_view(author_group['stories'][0], request.user)

        # Prepare stories json payload for client-side player
        stories_data = [
            {
                'id': s.id,
                'media_url': s.file_url,
                'is_video': s.is_video,
                'caption': s.caption,
                'created_at': s.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'views_count': s.views_count,
            }
            for s in author_group['stories']
        ]

        context = {
            'author': author,
            'stories': author_group['stories'],
            'stories_json': json.dumps(stories_data),
            'is_self': request.user.is_authenticated and request.user.id == author.id,
        }
        return render(request, self.template_name, context)
