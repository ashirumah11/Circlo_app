from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment
from .services import CommentService


class CommentDetailAPIView(APIView):
    """Delete a comment."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Delete comment", responses={204: None, 403: OpenApiResponse(description="Forbidden")})
    def delete(self, request, pk: int, *args, **kwargs):
        try:
            comment = Comment.objects.select_related('user', 'post__author').get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            CommentService.delete_comment(comment=comment, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DjangoValidationError as e:
            msg = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(msg, status=status.HTTP_403_FORBIDDEN)


class CommentLikeToggleAPIView(APIView):
    """Toggle like on a comment."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Toggle like on comment", responses={200: OpenApiResponse(description="Like toggled")})
    def post(self, request, pk: int, *args, **kwargs):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_liked, likes_count = CommentService.toggle_comment_like(comment=comment, user=request.user)
        return Response({
            'comment_id': comment.id,
            'is_liked': is_liked,
            'likes_count': likes_count,
        }, status=status.HTTP_200_OK)
