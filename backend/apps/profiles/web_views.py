from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.services import ProfileService


class ProfileWebView(View):
    """
    Renders public or private profile for a user.
    """
    template_name = 'profiles/profile.html'

    def get(self, request, identifier):
        clean_handle = identifier.lstrip('@')
        profile_user = ProfileService.get_profile_by_id_or_username(clean_handle)
        if not profile_user or not profile_user.is_active:
            raise Http404("Profile does not exist.")

        is_self = request.user.is_authenticated and request.user == profile_user

        from apps.social.services import SocialService
        from apps.bookmarks.services import BookmarkService

        follow_status = SocialService.get_follow_status(request.user, profile_user)
        is_following = follow_status == 'following'
        is_requested = follow_status == 'requested'

        saved_posts = []
        if is_self:
            saved_posts = BookmarkService.get_user_bookmarked_posts(profile_user)

        context = {
            'profile_user': profile_user,
            'is_self': is_self,
            'posts_count': profile_user.posts_count,
            'followers_count': profile_user.followers_count,
            'following_count': profile_user.following_count,
            'is_following': is_following,
            'is_requested': is_requested,
            'follow_status': follow_status,
            'saved_posts': saved_posts,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class ProfileEditWebView(View):
    """
    Renders and processes user profile editing.
    """
    template_name = 'profiles/edit.html'

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})

    def post(self, request):
        data = {
            'full_name': request.POST.get('full_name', ''),
            'bio': request.POST.get('bio', ''),
            'website': request.POST.get('website', ''),
            'location': request.POST.get('location', ''),
            'is_private': request.POST.get('is_private') == 'on',
        }

        try:
            ProfileService.update_profile(
                user=request.user,
                data=data,
                files=request.FILES
            )
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile-view', identifier=request.user.username)
        except Exception as e:
            messages.error(request, f'Failed to update profile: {e}')
            return render(request, self.template_name, {'user': request.user})


@method_decorator(login_required, name='dispatch')
class MyProfileRedirectWebView(View):
    """
    Redirects to the logged in user's profile handle.
    """
    def get(self, request):
        return redirect('profile-view', identifier=request.user.username)
