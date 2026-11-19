from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListAPIView(generics.ListAPIView):
    """
    Returns user notifications, ordered latest first.
    Query param `unread=true` filters to unread only.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List user notifications",
        parameters=[
            OpenApiParameter(name='unread', description='Filter unread only (true/false)', required=False, type=bool)
        ]
    )
    def get_queryset(self):
        unread_only = self.request.query_params.get('unread', '').lower() in ('true', '1')
        return NotificationService.get_user_notifications(self.request.user, unread_only=unread_only)


class NotificationDetailAPIView(APIView):
    """
    Mark an individual notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Mark notification as read",
        responses={200: OpenApiResponse(description="Marked as read"), 404: OpenApiResponse(description="Not found")}
    )
    def patch(self, request, pk, *args, **kwargs):
        success = NotificationService.mark_as_read(notification_id=pk, user=request.user)
        if not success:
            return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)


class NotificationReadAllAPIView(APIView):
    """
    Mark all notifications for the authenticated user as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Mark all notifications as read",
        responses={200: OpenApiResponse(description="All notifications marked as read")}
    )
    def post(self, request, *args, **kwargs):
        updated_count = NotificationService.mark_all_as_read(user=request.user)
        return Response({
            'message': f"Marked {updated_count} notifications as read.",
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)


class NotificationUnreadCountAPIView(APIView):
    """
    Returns the quick count of unread notifications for badge rendering.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get unread notifications count",
        responses={200: OpenApiResponse(description="Unread count")}
    )
    def get(self, request, *args, **kwargs):
        count = NotificationService.get_unread_count(request.user)
        return Response({'unread_count': count}, status=status.HTTP_200_OK)
