from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Comment, CommentLike
from apps.posts.models import Post

User = get_user_model()


class CommentService:
    """Handles business operations for post comments, threaded replies, and comment likes."""

    @staticmethod
    def create_comment(
        post: Post,
        user: User,
        text: str,
        parent_id: Optional[int] = None
    ) -> Comment:
        clean_text = text.strip()
        if not clean_text:
            raise ValidationError({'text': 'Comment cannot be empty.'})

        parent = None
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id, post=post)
            except Comment.DoesNotExist:
                raise ValidationError({'parent': 'The comment you are replying to does not exist.'})

        comment = Comment.objects.create(
            post=post,
            user=user,
            parent=parent,
            text=clean_text
        )
        return comment

    @staticmethod
    def delete_comment(comment: Comment, user: User) -> None:
        """Allows comment author or post author to delete the comment."""
        if comment.user != user and comment.post.author != user and not user.is_staff:
            raise ValidationError({'permission': 'You do not have permission to delete this comment.'})
        comment.delete()

    @staticmethod
    def toggle_comment_like(comment: Comment, user: User) -> Tuple[bool, int]:
        like_qs = CommentLike.objects.filter(comment=comment, user=user)
        if like_qs.exists():
            like_qs.delete()
            return False, comment.likes.count()
        else:
            CommentLike.objects.create(comment=comment, user=user)
            return True, comment.likes.count()
