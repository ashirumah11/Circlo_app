import os
import re
from typing import Any, List, Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet

from .models import Hashtag, Post, PostLike, PostMedia

User = get_user_model()

ALLOWED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_VIDEO_EXTS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class PostMediaValidator:
    """Validates file extensions, types, and sizes for uploads."""

    @staticmethod
    def validate_and_categorize(file_obj) -> str:
        name = file_obj.name.lower()
        ext = os.path.splitext(name)[1]

        if file_obj.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(f"File {file_obj.name} exceeds the maximum limit of 50MB.")

        if ext in ALLOWED_IMAGE_EXTS:
            return PostMedia.MEDIA_TYPE_IMAGE
        elif ext in ALLOWED_VIDEO_EXTS:
            return PostMedia.MEDIA_TYPE_VIDEO
        else:
            raise ValidationError(
                f"Unsupported file type for {file_obj.name}. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS))}"
            )


class PostService:
    """Handles business operations for posts, media, hashtags and likes."""

    @staticmethod
    def extract_and_sync_hashtags(post: Post) -> None:
        """Finds all #tags in caption, creates records, and links them."""
        tags = set(re.findall(r'#([A-Za-z0-9_]+)', post.caption))
        post.hashtags.clear()
        for tag in tags:
            tag_name = tag.lower().strip()
            hashtag, _ = Hashtag.objects.get_or_create(name=tag_name)
            post.hashtags.add(hashtag)

    @staticmethod
    @transaction.atomic
    def create_post(
        author: User,
        caption: str = '',
        files: Optional[List[Any]] = None,
        location: str = ''
    ) -> Post:
        """
        Creates a post with multiple media attachments and hashtag associations.
        """
        if not files or len(files) == 0:
            raise ValidationError({'media': 'At least one photo or video is required to create a post.'})

        # Validate all files before creating any records
        validated_media = []
        for index, file_obj in enumerate(files):
            media_type = PostMediaValidator.validate_and_categorize(file_obj)
            validated_media.append((file_obj, media_type, index))

        post = Post.objects.create(
            author=author,
            caption=caption.strip(),
            location=location.strip()
        )

        for file_obj, media_type, order in validated_media:
            PostMedia.objects.create(
                post=post,
                file=file_obj,
                media_type=media_type,
                order=order
            )

        PostService.extract_and_sync_hashtags(post)
        return post

    @staticmethod
    @transaction.atomic
    def update_post(
        post: Post,
        user: User,
        caption: Optional[str] = None,
        location: Optional[str] = None
    ) -> Post:
        """Updates caption or location of an existing post."""
        if post.author != user:
            raise ValidationError({'permission': 'You do not have permission to edit this post.'})

        update_fields = ['updated_at']
        if caption is not None:
            post.caption = caption.strip()
            update_fields.append('caption')
            PostService.extract_and_sync_hashtags(post)

        if location is not None:
            post.location = location.strip()
            update_fields.append('location')

        post.save(update_fields=update_fields)
        return post

    @staticmethod
    def delete_post(post: Post, user: User) -> None:
        """Deletes a post with owner authorization check."""
        if post.author != user and not user.is_staff:
            raise ValidationError({'permission': 'You do not have permission to delete this post.'})
        post.delete()

    @staticmethod
    def toggle_like(post: Post, user: User) -> Tuple[bool, int]:
        """
        Toggles like status on a post.
        Returns: (is_liked: bool, total_likes: int)
        """
        like_qs = PostLike.objects.filter(post=post, user=user)
        if like_qs.exists():
            like_qs.delete()
            return False, post.likes.count()
        else:
            PostLike.objects.create(post=post, user=user)
            try:
                from apps.notifications.services import NotificationService
                NotificationService.create_notification(
                    recipient=post.author,
                    actor=user,
                    verb='like_post',
                    text='liked your post.',
                    target_id=post.id,
                    target_url=f"/posts/{post.id}/"
                )
            except Exception:
                pass
            return True, post.likes.count()

    @staticmethod
    def get_feed_for_user(user: Optional[User], filter_type: str = 'following') -> QuerySet[Post]:
        """
        Returns personalized feed:
        - If authenticated & following accounts exist: posts from followed accounts + own posts
        - If not following anyone yet or filter_type == 'latest': latest public posts
        """
        queryset = Post.objects.select_related('author').prefetch_related('media', 'likes', 'comments')

        if user and user.is_authenticated and filter_type == 'following':
            following_ids = list(
                user.following_relations.filter(is_pending=False).values_list('following_id', flat=True)
            )
            if following_ids:
                author_ids = set(following_ids) | {user.id}
                queryset = queryset.filter(author_id__in=author_ids, author__is_active=True).order_by('-created_at')
            else:
                # Fallback for new users: show active public posts
                queryset = queryset.filter(author__is_active=True, author__is_private=False).order_by('-created_at')
        else:
            queryset = queryset.filter(author__is_active=True, author__is_private=False).order_by('-created_at')

        return queryset
