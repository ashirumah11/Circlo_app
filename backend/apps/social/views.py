from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Block, Follow
from .serializers import FollowRequestSerializer
from .services import SocialService
from apps.accounts.serializers import UserSummarySerializer

User = get_user_model()


class PendingFollowRequestsAPIView(generics.ListAPIView):
    """
    Returns incoming pending follow requests for the authenticated user's private account.
    """
    serializer_class = FollowRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List incoming follow requests")
    def get_queryset(self):
        return SocialService.get_pending_requests(self.request.user)


class AcceptFollowRequestAPIView(APIView):
    """
    Accept an incoming follow request by request ID or follower user ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Accept follow request",
        responses={200: OpenApiResponse(description="Follow request approved")}
    )
    def post(self, request, pk, *args, **kwargs):
        # Support either Follow.id or follower User.id
        follow = Follow.objects.filter(following=request.user, is_pending=True).filter(
            id=pk
        ).first()

        if not follow:
            # Fallback check if pk is follower_id
            follow = Follow.objects.filter(following=request.user, follower_id=pk, is_pending=True).first()

        if not follow:
            return Response({'detail': 'Pending follow request not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            SocialService.accept_follow_request(target_user=request.user, follower=follow.follower)
            return Response({
                'message': f"Accepted follow request from @{follow.follower.username}.",
                'follower_id': follow.follower_id,
                'status': 'following'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RejectFollowRequestAPIView(APIView):
    """
    Reject or delete an incoming follow request.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Reject follow request",
        responses={200: OpenApiResponse(description="Follow request rejected")}
    )
    def post(self, request, pk, *args, **kwargs):
        follow = Follow.objects.filter(following=request.user, is_pending=True).filter(
            id=pk
        ).first()

        if not follow:
            follow = Follow.objects.filter(following=request.user, follower_id=pk, is_pending=True).first()

        if not follow:
            return Response({'detail': 'Pending follow request not found.'}, status=status.HTTP_404_NOT_FOUND)

        follower = follow.follower
        SocialService.reject_follow_request(target_user=request.user, follower=follower)
        return Response({
            'message': f"Rejected follow request from @{follower.username}.",
            'status': 'rejected'
        }, status=status.HTTP_200_OK)


class BlockedUsersListAPIView(generics.ListAPIView):
    """
    Returns list of users blocked by the authenticated user.
    """
    serializer_class = UserSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List blocked users")
    def get_queryset(self):
        blocked_ids = Block.objects.filter(blocker=self.request.user).values_list('blocked_id', flat=True)
        return User.objects.filter(id__in=blocked_ids, is_active=True).order_by('username')
