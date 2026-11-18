from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Story
from .serializers import (
    StoryGroupSerializer,
    StorySerializer,
    StoryUploadSerializer,
    StoryViewSerializer,
)
from .services import StoryService


class StoriesListCreateAPIView(APIView):
    """
    Endpoint for stories tray retrieval and uploading new stories.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Get active stories feed",
        responses={200: StoryGroupSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        viewer = request.user if request.user.is_authenticated else None
        groups = StoryService.get_active_stories_grouped(viewer=viewer)
        serializer = StoryGroupSerializer(groups, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Upload a new story",
        request=StoryUploadSerializer,
        responses={201: StorySerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = StoryUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            story = StoryService.create_story(
                author=request.user,
                file=serializer.validated_data['file'],
                caption=serializer.validated_data.get('caption', '')
            )
            out_serializer = StorySerializer(story, context={'request': request})
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StoryDetailAPIView(APIView):
    """
    Retrieve or delete an individual story.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Get story details",
        responses={200: StorySerializer, 404: OpenApiResponse(description="Story not found")}
    )
    def get(self, request, pk, *args, **kwargs):
        story = Story.objects.filter(pk=pk).select_related('author').first()
        if not story or story.is_expired:
            return Response({'detail': 'Story not found or expired.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StorySerializer(story, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete story",
        responses={204: OpenApiResponse(description="Story deleted"), 403: OpenApiResponse(description="Forbidden")}
    )
    def delete(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        story = Story.objects.filter(pk=pk).first()
        if not story:
            return Response({'detail': 'Story not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            StoryService.delete_story(story, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)


class StoryRecordViewAPIView(APIView):
    """
    Mark story as viewed by the authenticated viewer.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Record story view",
        responses={200: OpenApiResponse(description="View recorded")}
    )
    def post(self, request, pk, *args, **kwargs):
        story = Story.objects.filter(pk=pk).first()
        if not story or story.is_expired:
            return Response({'detail': 'Story not found or expired.'}, status=status.HTTP_404_NOT_FOUND)

        is_new_view = StoryService.record_view(story=story, viewer=request.user)
        return Response({
            'story_id': story.id,
            'is_new_view': is_new_view,
            'views_count': story.views_count
        }, status=status.HTTP_200_OK)


class StoryViewersListAPIView(generics.ListAPIView):
    """
    List of viewers who viewed a story (author only).
    """
    serializer_class = StoryViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List viewers of a story")
    def get_queryset(self):
        pk = self.kwargs['pk']
        story = generics.get_object_or_404(Story, pk=pk)
        return StoryService.get_story_viewers(story=story, requester=self.request.user)
