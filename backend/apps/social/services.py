from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet

from .models import Block, Follow, Mute

User = get_user_model()


class SocialService:
    """
    Business service layer managing user relationships:
    - Follow & Unfollow
    - Private account follow requests (request, accept, reject)
    - Block & Mute
    - Follower/Following queries
    """

    @staticmethod
    def get_follow_status(viewer: Optional[User], target_user: User) -> str:
        """
        Returns relationship status of viewer towards target_user:
        'self', 'following', 'requested', or 'none'
        """
        if not viewer or not viewer.is_authenticated:
            return 'none'
        if viewer.id == target_user.id:
            return 'self'

        follow = Follow.objects.filter(follower=viewer, following=target_user).first()
        if not follow:
            return 'none'
        return 'requested' if follow.is_pending else 'following'

    @classmethod
    def toggle_follow(cls, follower: User, target_user: User) -> dict:
        """
        Toggles follow state:
        - If following or requested: unfollows / withdraws request.
        - If not following:
            - If target is private: creates pending request (is_pending=True).
            - If target is public: immediately follows (is_pending=False).
        """
        if follower.id == target_user.id:
            raise ValidationError("You cannot follow yourself.")

        # Check block status
        if cls.is_blocked(follower, target_user):
            raise ValidationError("You cannot interact with this account.")

        existing_follow = Follow.objects.filter(follower=follower, following=target_user).first()

        if existing_follow:
            existing_follow.delete()
            return {
                'status': 'none',
                'is_following': False,
                'is_pending': False,
                'followers_count': target_user.followers_count,
                'message': f"Unfollowed @{target_user.username}."
            }

        # Handle private account
        if target_user.is_private:
            Follow.objects.create(follower=follower, following=target_user, is_pending=True)
            try:
                from apps.notifications.services import NotificationService
                NotificationService.create_notification(
                    recipient=target_user,
                    actor=follower,
                    verb='follow_request',
                    text='requested to follow you.',
                    target_id=follower.id,
                    target_url=f"/@{follower.username}/"
                )
            except Exception:
                pass
            return {
                'status': 'requested',
                'is_following': False,
                'is_pending': True,
                'followers_count': target_user.followers_count,
                'message': f"Follow request sent to @{target_user.username}."
            }
        else:
            Follow.objects.create(follower=follower, following=target_user, is_pending=False)
            try:
                from apps.notifications.services import NotificationService
                NotificationService.create_notification(
                    recipient=target_user,
                    actor=follower,
                    verb='follow',
                    text='started following you.',
                    target_id=follower.id,
                    target_url=f"/@{follower.username}/"
                )
            except Exception:
                pass
            return {
                'status': 'following',
                'is_following': True,
                'is_pending': False,
                'followers_count': target_user.followers_count,
                'message': f"You are now following @{target_user.username}."
            }

    @staticmethod
    def accept_follow_request(target_user: User, follower: User) -> Follow:
        """
        Target user of a private account accepts an incoming follow request.
        """
        follow = Follow.objects.filter(follower=follower, following=target_user, is_pending=True).first()
        if not follow:
            raise ValidationError("Pending follow request not found.")

        follow.is_pending = False
        follow.save(update_fields=['is_pending', 'updated_at'])

        try:
            from apps.notifications.services import NotificationService
            NotificationService.create_notification(
                recipient=follower,
                actor=target_user,
                verb='follow',
                text='accepted your follow request.',
                target_id=target_user.id,
                target_url=f"/@{target_user.username}/"
            )
        except Exception:
            pass

        return follow

    @staticmethod
    def reject_follow_request(target_user: User, follower: User) -> bool:
        """
        Target user of a private account rejects an incoming follow request.
        """
        deleted_count, _ = Follow.objects.filter(follower=follower, following=target_user, is_pending=True).delete()
        if deleted_count == 0:
            raise ValidationError("Pending follow request not found.")
        return True

    @staticmethod
    def get_followers(user: User, viewer: Optional[User] = None) -> QuerySet[User]:
        """
        Returns active approved followers of user, excluding blocked users.
        """
        blocked_ids = set()
        if viewer and viewer.is_authenticated:
            blocked_ids = set(
                Block.objects.filter(Q(blocker=viewer) | Q(blocked=viewer))
                .values_list('blocker_id', 'blocked_id')
            )
            # Flatten tuples
            flattened = {uid for pair in blocked_ids for uid in pair if uid != viewer.id}
            blocked_ids = flattened

        queryset = User.objects.filter(
            following_relations__following=user,
            following_relations__is_pending=False,
            is_active=True
        ).exclude(id__in=blocked_ids).distinct().order_by('-following_relations__created_at')
        return queryset

    @staticmethod
    def get_following(user: User, viewer: Optional[User] = None) -> QuerySet[User]:
        """
        Returns accounts followed by user, excluding blocked users.
        """
        blocked_ids = set()
        if viewer and viewer.is_authenticated:
            blocked_pairs = Block.objects.filter(Q(blocker=viewer) | Q(blocked=viewer)).values_list('blocker_id', 'blocked_id')
            blocked_ids = {uid for pair in blocked_pairs for uid in pair if uid != viewer.id}

        queryset = User.objects.filter(
            follower_relations__follower=user,
            follower_relations__is_pending=False,
            is_active=True
        ).exclude(id__in=blocked_ids).distinct().order_by('-follower_relations__created_at')
        return queryset

    @staticmethod
    def get_pending_requests(user: User) -> QuerySet[Follow]:
        """
        Returns incoming pending follow requests for the target user.
        """
        return Follow.objects.filter(following=user, is_pending=True).select_related('follower').order_by('-created_at')

    @classmethod
    def toggle_block(cls, blocker: User, target_user: User) -> Tuple[bool, str]:
        """
        Toggles block on target_user.
        If blocking: breaks any follow connection in both directions.
        """
        if blocker.id == target_user.id:
            raise ValidationError("You cannot block yourself.")

        existing = Block.objects.filter(blocker=blocker, blocked=target_user).first()
        if existing:
            existing.delete()
            return False, f"Unblocked @{target_user.username}."

        Block.objects.create(blocker=blocker, blocked=target_user)
        # Sever follow relations both directions
        Follow.objects.filter(
            Q(follower=blocker, following=target_user) |
            Q(follower=target_user, following=blocker)
        ).delete()
        return True, f"Blocked @{target_user.username}."

    @staticmethod
    def is_blocked(user_a: User, user_b: User) -> bool:
        """Checks if a blocking relation exists in either direction."""
        if not user_a or not user_b or not user_a.is_authenticated or not user_b.is_authenticated:
            return False
        return Block.objects.filter(
            Q(blocker=user_a, blocked=user_b) |
            Q(blocker=user_b, blocked=user_a)
        ).exists()

    @staticmethod
    def toggle_mute(muter: User, target_user: User) -> Tuple[bool, str]:
        """Toggles muting target_user."""
        if muter.id == target_user.id:
            raise ValidationError("You cannot mute yourself.")

        existing = Mute.objects.filter(muter=muter, muted=target_user).first()
        if existing:
            existing.delete()
            return False, f"Unmuted @{target_user.username}."

        Mute.objects.create(muter=muter, muted=target_user)
        return True, f"Muted @{target_user.username}."
