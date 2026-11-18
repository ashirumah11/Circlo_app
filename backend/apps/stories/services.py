import os
from datetime import timedelta
from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Story, StoryView
from apps.social.models import Block

User = get_user_model()

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class StoryService:
    """
    Business service layer managing ephemeral 24-hour stories:
    - Uploading and media validation
    - Feed tray grouping (unviewed vs viewed)
    - View tracking and viewer analytics
    - Story expiration and cleanup
    """

    @classmethod
    def create_story(cls, author: User, file, caption: str = "") -> Story:
        if not file:
            raise ValidationError("A photo or video file is required to post a story.")

        if file.size > MAX_FILE_SIZE:
            raise ValidationError(f"File '{file.name}' exceeds the maximum allowed size of 50MB.")

        ext = os.path.splitext(file.name)[1].lower()
        content_type = getattr(file, 'content_type', '')

        if ext in ALLOWED_IMAGE_EXTENSIONS or content_type.startswith('image/'):
            media_type = 'image'
        elif ext in ALLOWED_VIDEO_EXTENSIONS or content_type.startswith('video/'):
            media_type = 'video'
        else:
            raise ValidationError(
                f"Unsupported format '{ext}'. Allowed formats: JPG, PNG, WEBP, GIF, MP4, MOV, WEBM."
            )

        now = timezone.now()
        expires_at = now + timedelta(hours=24)

        return Story.objects.create(
            author=author,
            media_file=file,
            media_type=media_type,
            caption=caption.strip()[:255],
            expires_at=expires_at
        )

    @classmethod
    def get_active_stories_grouped(cls, viewer: Optional[User]) -> List[Dict[str, Any]]:
        """
        Returns active stories grouped by author for the story tray.
        Active = expires_at > timezone.now() and author is active.
        """
        now = timezone.now()
        base_qs = Story.objects.filter(
            expires_at__gt=now,
            author__is_active=True
        ).select_related('author').prefetch_related('views')

        if not viewer or not viewer.is_authenticated:
            # Public active stories only
            active_stories = base_qs.filter(author__is_private=False).order_by('created_at')
            author_map = {}
            for s in active_stories:
                if s.author_id not in author_map:
                    author_map[s.author_id] = {
                        'author': s.author,
                        'stories': [],
                        'has_unviewed': True,
                        'is_self': False,
                    }
                author_map[s.author_id]['stories'].append(s)
            return list(author_map.values())

        # Exclude blocked users
        blocked_ids = set()
        blocked_pairs = Block.objects.filter(Q(blocker=viewer) | Q(blocked=viewer)).values_list('blocker_id', 'blocked_id')
        blocked_ids = {uid for pair in blocked_pairs for uid in pair if uid != viewer.id}

        # Authors allowed: followed accounts + self
        followed_ids = set(
            viewer.following_relations.filter(is_pending=False).values_list('following_id', flat=True)
        )
        allowed_author_ids = (followed_ids | {viewer.id}) - blocked_ids

        active_stories = base_qs.filter(author_id__in=allowed_author_ids).order_by('created_at')

        # Viewer's viewed story IDs
        viewed_story_ids = set(
            viewer.story_views.filter(story__expires_at__gt=now).values_list('story_id', flat=True)
        )

        author_map = {}
        for s in active_stories:
            if s.author_id not in author_map:
                is_self = s.author_id == viewer.id
                author_map[s.author_id] = {
                    'author': s.author,
                    'stories': [],
                    'has_unviewed': False if is_self else True,
                    'is_self': is_self,
                }
            author_map[s.author_id]['stories'].append(s)
            if not author_map[s.author_id]['is_self']:
                # If any story is not viewed, mark group as has_unviewed
                if s.id not in viewed_story_ids:
                    author_map[s.author_id]['has_unviewed'] = True

        # For groups where all stories were viewed, ensure has_unviewed is False
        for aid, data in author_map.items():
            if not data['is_self']:
                all_viewed = all(story.id in viewed_story_ids for story in data['stories'])
                data['has_unviewed'] = not all_viewed

        # Sort order:
        # 1. Self first
        # 2. Authors with unviewed stories
        # 3. Authors with all-viewed stories
        groups = list(author_map.values())
        groups.sort(key=lambda g: (not g['is_self'], not g['has_unviewed']))
        return groups

    @staticmethod
    def record_view(story: Story, viewer: User) -> bool:
        """
        Records a story view. Does not record self-views.
        Returns True if a new view was recorded, False if already viewed or author.
        """
        if viewer.id == story.author_id:
            return False

        _, created = StoryView.objects.get_or_create(story=story, viewer=viewer)
        return created

    @staticmethod
    def get_story_viewers(story: Story, requester: User):
        """
        Returns viewers list for a story. Only the story author or staff can view.
        """
        if requester.id != story.author_id and not requester.is_staff:
            raise PermissionDenied("You can only view viewers of your own stories.")
        return story.views.select_related('viewer').order_by('-viewed_at')

    @staticmethod
    def delete_story(story: Story, user: User) -> bool:
        """
        Deletes a story if user is the author or staff.
        """
        if user.id != story.author_id and not user.is_staff:
            raise PermissionDenied("You do not have permission to delete this story.")
        story.delete()
        return True
