from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UnifiedSearchResultSerializer
from .services import SearchService
from apps.accounts.serializers import UserSummarySerializer
from apps.posts.serializers import HashtagSerializer, PostSerializer


class UnifiedSearchAPIView(APIView):
    """
    Search endpoint supporting user lookup, hashtag exploration, and post discovery.
    Query parameters:
    - `q`: search query string (e.g. "photography", "@jane", "#sunset")
    - `type`: optional filter: 'all' (default), 'users', 'hashtags', 'posts'
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Search accounts, hashtags, and posts",
        parameters=[
            OpenApiParameter(name='q', description='Search term', required=True, type=str),
            OpenApiParameter(name='type', description='Filter results by type', required=False, type=str, enum=['all', 'users', 'hashtags', 'posts']),
        ],
        responses={200: UnifiedSearchResultSerializer}
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all').lower()

        if not query:
            return Response({
                'query': '',
                'users': [],
                'hashtags': [],
                'posts': []
            }, status=status.HTTP_200_OK)

        viewer = request.user if request.user.is_authenticated else None

        if search_type == 'users':
            users = SearchService.search_users(query, viewer=viewer)
            serializer = UserSummarySerializer(users, many=True, context={'request': request})
            return Response({'query': query, 'users': serializer.data}, status=status.HTTP_200_OK)

        if search_type == 'hashtags':
            tags = SearchService.search_hashtags(query)
            serializer = HashtagSerializer(tags, many=True)
            return Response({'query': query, 'hashtags': serializer.data}, status=status.HTTP_200_OK)

        if search_type == 'posts':
            posts = SearchService.search_posts(query, viewer=viewer)
            serializer = PostSerializer(posts, many=True, context={'request': request})
            return Response({'query': query, 'posts': serializer.data}, status=status.HTTP_200_OK)

        # Unified search
        results = SearchService.unified_search(query, viewer=viewer)
        return Response({
            'query': query,
            'users': UserSummarySerializer(results['users'], many=True, context={'request': request}).data,
            'hashtags': HashtagSerializer(results['hashtags'], many=True).data,
            'posts': PostSerializer(results['posts'], many=True, context={'request': request}).data,
        }, status=status.HTTP_200_OK)


class ExploreAPIView(APIView):
    """
    Explore discovery feed returning trending posts ordered by popularity & engagement.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Explore trending posts grid",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        viewer = request.user if request.user.is_authenticated else None
        posts = SearchService.get_explore_posts(viewer=viewer)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
