from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .services import NotificationService


@method_decorator(login_required, name='dispatch')
class NotificationsWebView(View):
    """
    Renders notifications page with filters (All, Unread) and mark-read support.
    """
    template_name = 'notifications/notifications.html'

    def get(self, request):
        filter_type = request.GET.get('filter', 'all')
        unread_only = (filter_type == 'unread')

        notifications = NotificationService.get_user_notifications(request.user, unread_only=unread_only)
        unread_count = NotificationService.get_unread_count(request.user)

        return render(request, self.template_name, {
            'notifications': notifications,
            'filter_type': filter_type,
            'unread_count': unread_count,
        })

    def post(self, request):
        action = request.POST.get('action')
        if action == 'mark_all_read':
            NotificationService.mark_all_as_read(request.user)
        return redirect('notifications_web:notifications-list')
