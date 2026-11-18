from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import UserProfileSerializer, UserSummarySerializer
from apps.accounts.services import ProfileService
from apps.social.services import SocialService

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProfileListAPIView(generics.ListAPIView):
    """
    Public endpoint to discover and search profiles.
    Supports filtering by ?search=<term> (matches username or full_name).
    """
    serializer_class = UserSummarySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List and search profiles",
        parameters=[
            OpenApiParameter(name='search', description='Search username or full name', required=False, type=str)
        ]
    )
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).order_by('-date_joined')
        search_query = self.request.query_params.get('search')
        if search_query:
            clean_term = search_query.strip().lstrip('@')
            queryset = queryset.filter(
                Q(username__icontains=clean_term) | Q(full_name__icontains=clean_term)
            )
        return queryset


class ProfileDetailAPIView(APIView):
    """
    Endpoint to retrieve or update an individual profile.
    Accepts user ID or @username handle.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, identifier: str) -> User:
        user = ProfileService.get_profile_by_id_or_username(identifier)
        if not user or not user.is_active:
            from rest_framework.exceptions import NotFound
            raise NotFound(detail="User profile not found.")
        return user

    @extend_schema(
        summary="Retrieve user profile",
        responses={
            200: UserProfileSerializer,
            404: OpenApiResponse(description="User not found"),
        }
    )
    def get(self, request, id, *args, **kwargs):
        user = self.get_object(str(id))
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update profile",
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            403: OpenApiResponse(description="Cannot edit someone else's profile"),
            404: OpenApiResponse(description="User not found"),
        }
    )
    def patch(self, request, id, *args, **kwargs):
        user = self.get_object(str(id))
        if request.user != user:
            raise PermissionDenied(detail="You do not have permission to modify this profile.")

        updated_user = ProfileService.update_profile(
            user=user,
            data=request.data,
            files=request.FILES
        )
        serializer = UserProfileSerializer(updated_user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileFollowersAPIView(APIView):
    """
    Returns followers list for profile.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Get profile followers",
        responses={200: UserSummarySerializer(many=True)}
    )
    def get(self, request, id, *args, **kwargs):
        user = ProfileService.get_profile_by_id_or_username(str(id))
        if not user or not user.is_active:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        followers_qs = SocialService.get_followers(user=user, viewer=request.user)
        serializer = UserSummarySerializer(followers_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileFollowingAPIView(APIView):
    """
    Returns following list for profile.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Get accounts followed by user",
        responses={200: UserSummarySerializer(many=True)}
    )
    def get(self, request, id, *args, **kwargs):
        user = ProfileService.get_profile_by_id_or_username(str(id))
        if not user or not user.is_active:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        following_qs = SocialService.get_following(user=user, viewer=request.user)
        serializer = UserSummarySerializer(following_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileFollowToggleAPIView(APIView):
    """
    Follow or unfollow user toggle endpoint.
    Handles private account follow requests automatically.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Follow/unfollow user",
        responses={200: OpenApiResponse(description="Follow status toggled")}
    )
    def post(self, request, id, *args, **kwargs):
        target_user = ProfileService.get_profile_by_id_or_username(str(id))
        if not target_user or not target_user.is_active:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_user == request.user:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = SocialService.toggle_follow(follower=request.user, target_user=target_user)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileBlockToggleAPIView(APIView):
    """
    Block or unblock user endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Block/unblock user",
        responses={200: OpenApiResponse(description="Block status toggled")}
    )
    def post(self, request, id, *args, **kwargs):
        target_user = ProfileService.get_profile_by_id_or_username(str(id))
        if not target_user or not target_user.is_active:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_user == request.user:
            return Response({'detail': 'You cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            is_blocked, msg = SocialService.toggle_block(blocker=request.user, target_user=target_user)
            return Response({
                'is_blocked': is_blocked,
                'message': msg,
                'target_username': target_user.username
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
