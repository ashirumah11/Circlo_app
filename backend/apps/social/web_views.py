from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Follow
from .services import SocialService

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class FollowToggleWebView(View):
    """
    Handles follow/unfollow button submissions from web pages.
    Supports both regular POST redirection and AJAX JSON response.
    """
    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk, is_active=True)
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'

        try:
            result = SocialService.toggle_follow(follower=request.user, target_user=target_user)
            messages.success(request, result['message'])

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse(result)

        except Exception as e:
            messages.error(request, str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)

        return redirect(next_url)


@method_decorator(login_required, name='dispatch')
class FollowRequestsWebView(View):
    """
    Renders incoming follow requests for the authenticated user.
    """
    template_name = 'social/requests.html'

    def get(self, request):
        pending_requests = SocialService.get_pending_requests(request.user)
        return render(request, self.template_name, {'requests': pending_requests})


@method_decorator(login_required, name='dispatch')
class FollowRequestActionWebView(View):
    """
    Accept or reject incoming follow request from web template.
    """
    def post(self, request, pk):
        action = request.POST.get('action', 'accept')
        follow = get_object_or_404(Follow, pk=pk, following=request.user, is_pending=True)
        follower = follow.follower

        if action == 'accept':
            SocialService.accept_follow_request(target_user=request.user, follower=follower)
            messages.success(request, f"Accepted follow request from @{follower.username}.")
        elif action == 'reject':
            SocialService.reject_follow_request(target_user=request.user, follower=follower)
            messages.info(request, f"Declined follow request from @{follower.username}.")

        return redirect('social-web:follow-requests')
