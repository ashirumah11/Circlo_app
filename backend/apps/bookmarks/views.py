from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Bookmark
from .serializers import BookmarkSerializer
from .services import BookmarkService
from apps.posts.models import Post
from apps.posts.serializers import PostSerializer


class BookmarkListAPIView(generics.ListAPIView):
    """
    Returns all posts saved / bookmarked by the authenticated user.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List user saved posts")
    def get_queryset(self):
        return BookmarkService.get_user_bookmarked_posts(self.request.user)


class BookmarkToggleAPIView(APIView):
    """
    Toggle saving/bookmarking a post.
    Accepts either post_id in URL (/posts/<id>/bookmark/) or in request body (/bookmarks/).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Toggle post bookmark/save",
        responses={200: OpenApiResponse(description="Post saved or removed from saved")}
    )
    def post(self, request, pk=None, *args, **kwargs):
        post_id = pk or request.data.get('post_id')
        if not post_id:
            return Response({'detail': 'Post ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        post = Post.objects.filter(pk=post_id, author__is_active=True).first()
        if not post:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_bookmarked, message = BookmarkService.toggle_bookmark(user=request.user, post=post)
        return Response({
            'is_bookmarked': is_bookmarked,
            'message': message,
            'post_id': post.id
        }, status=status.HTTP_200_OK)
