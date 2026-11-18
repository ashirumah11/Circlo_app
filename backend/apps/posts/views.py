from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post
from .serializers import PostCreateSerializer, PostSerializer
from .services import PostService
from apps.comments.models import Comment
from apps.comments.serializers import CommentCreateSerializer, CommentSerializer
from apps.comments.services import CommentService


class StandardPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class PostListCreateAPIView(APIView):
    """
    List posts or create a new post with uploaded media.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="List posts",
        parameters=[
            OpenApiParameter(name='author', description='Filter by author username', required=False, type=str),
            OpenApiParameter(name='hashtag', description='Filter by hashtag', required=False, type=str),
        ],
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = Post.objects.select_related('author').prefetch_related('media', 'likes', 'comments')

        author_handle = request.query_params.get('author')
        if author_handle:
            queryset = queryset.filter(author__username__iexact=author_handle.lstrip('@'))

        hashtag = request.query_params.get('hashtag')
        if hashtag:
            queryset = queryset.filter(hashtags__name__iexact=hashtag.lstrip('#').lower())

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create new post",
        request=PostCreateSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(description="Validation error"),
        }
    )
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('media')
        caption = request.data.get('caption', '')
        location = request.data.get('location', '')

        try:
            post = PostService.create_post(
                author=request.user,
                caption=caption,
                files=files,
                location=location
            )
            serializer = PostSerializer(post, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            msg = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class PostDetailAPIView(APIView):
    """
    Retrieve, update or delete a specific post.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk: int) -> Post:
        try:
            return Post.objects.select_related('author').prefetch_related('media', 'likes', 'comments').get(pk=pk)
        except Post.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Post not found.")

    @extend_schema(summary="Get post details", responses={200: PostSerializer})
    def get(self, request, pk: int, *args, **kwargs):
        post = self.get_object(pk)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update post caption/location",
        responses={200: PostSerializer, 403: OpenApiResponse(description="Forbidden")}
    )
    def patch(self, request, pk: int, *args, **kwargs):
        post = self.get_object(pk)
        try:
            updated = PostService.update_post(
                post=post,
                user=request.user,
                caption=request.data.get('caption'),
                location=request.data.get('location')
            )
            serializer = PostSerializer(updated, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            msg = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(msg, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(summary="Delete post", responses={204: None, 403: OpenApiResponse(description="Forbidden")})
    def delete(self, request, pk: int, *args, **kwargs):
        post = self.get_object(pk)
        try:
            PostService.delete_post(post=post, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DjangoValidationError as e:
            msg = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(msg, status=status.HTTP_403_FORBIDDEN)


class PostLikeToggleAPIView(APIView):
    """
    Toggle like on a post. Returns whether current user likes the post and total likes count.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Toggle like on post", responses={200: OpenApiResponse(description="Like toggled")})
    def post(self, request, pk: int, *args, **kwargs):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_liked, likes_count = PostService.toggle_like(post=post, user=request.user)
        return Response({
            'post_id': post.id,
            'is_liked': is_liked,
            'likes_count': likes_count,
        }, status=status.HTTP_200_OK)


class FeedAPIView(APIView):
    """
    Personalized user feed endpoint.
    Returns posts with pagination, engagement data and author information.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Get user feed",
        parameters=[
            OpenApiParameter(name='filter', description="'following' or 'latest'", required=False, type=str)
        ],
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        filter_type = request.query_params.get('filter', 'following')
        queryset = PostService.get_feed_for_user(user=request.user, filter_type=filter_type)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class PostCommentsListCreateAPIView(APIView):
    """
    Get comments for a post or create a new comment / reply.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(summary="List post comments", responses={200: CommentSerializer(many=True)})
    def get(self, request, pk: int, *args, **kwargs):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve top-level comments (parent=None) with replies prefetched
        comments = post.comments.filter(parent=None).select_related('user').prefetch_related('replies__user', 'likes')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create comment on post",
        request=CommentCreateSerializer,
        responses={201: CommentSerializer}
    )
    def post(self, request, pk: int, *args, **kwargs):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = CommentService.create_comment(
                post=post,
                user=request.user,
                text=serializer.validated_data['text'],
                parent_id=serializer.validated_data.get('parent_id')
            )
            return Response(
                CommentSerializer(comment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except DjangoValidationError as e:
            msg = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
