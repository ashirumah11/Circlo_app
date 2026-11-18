from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .services import BookmarkService
from apps.posts.models import Post


@method_decorator(login_required, name='dispatch')
class BookmarkToggleWebView(View):
    """
    Handles bookmarking/saving a post from web pages.
    """
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author__is_active=True)
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'

        is_bookmarked, msg = BookmarkService.toggle_bookmark(user=request.user, post=post)
        messages.success(request, msg)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'is_bookmarked': is_bookmarked, 'message': msg})

        return redirect(next_url)


@method_decorator(login_required, name='dispatch')
class SavedPostsWebView(View):
    """
    Renders saved posts gallery for the logged-in user.
    """
    template_name = 'profiles/saved.html'

    def get(self, request):
        saved_posts = BookmarkService.get_user_bookmarked_posts(request.user)
        return render(request, self.template_name, {'posts': saved_posts})
