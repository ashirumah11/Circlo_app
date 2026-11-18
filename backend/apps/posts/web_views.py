from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Post
from .services import PostService
from apps.comments.services import CommentService
from apps.stories.services import StoryService

User = get_user_model()


class FeedWebView(View):
    """
    Renders the main Circlo feed page with stories tray,
    post engagement cards, and suggested users.
    """
    template_name = 'feed/feed.html'

    def get(self, request):
        feed_filter = request.GET.get('filter', 'following')
        posts_qs = PostService.get_feed_for_user(request.user, filter_type=feed_filter)

        # Suggested accounts (active accounts excluding current user)
        suggested_users = User.objects.filter(is_active=True)
        if request.user.is_authenticated:
            suggested_users = suggested_users.exclude(id=request.user.id)
        suggested_users = suggested_users.order_by('-date_joined')[:5]

        # Check liked & bookmarked posts for authenticated user for instant UI rendering
        liked_post_ids = set()
        bookmarked_post_ids = set()
        if request.user.is_authenticated:
            liked_post_ids = set(
                request.user.post_likes.filter(post__in=posts_qs[:50]).values_list('post_id', flat=True)
            )
            bookmarked_post_ids = set(
                request.user.bookmarks.filter(post__in=posts_qs[:50]).values_list('post_id', flat=True)
            )

        # Active stories for the stories tray
        story_groups = StoryService.get_active_stories_grouped(viewer=request.user)

        context = {
            'posts': posts_qs[:20],
            'feed_filter': feed_filter,
            'suggested_users': suggested_users,
            'liked_post_ids': liked_post_ids,
            'bookmarked_post_ids': bookmarked_post_ids,
            'story_groups': story_groups,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class PostCreateWebView(View):
    """Create post page with media upload and caption."""
    template_name = 'posts/create.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        files = request.FILES.getlist('media')
        caption = request.POST.get('caption', '')
        location = request.POST.get('location', '')

        if not files or len(files) == 0:
            messages.error(request, 'Please select at least one photo or video to upload.')
            return render(request, self.template_name, {'caption': caption, 'location': location})

        try:
            post = PostService.create_post(
                author=request.user,
                caption=caption,
                files=files,
                location=location
            )
            messages.success(request, 'Your post has been shared!')
            return redirect('post-detail-web', pk=post.id)
        except ValidationError as e:
            msg = e.message_dict.get('media', [str(e)])[0] if hasattr(e, 'message_dict') else str(e)
            messages.error(request, msg)
            return render(request, self.template_name, {'caption': caption, 'location': location})


class PostDetailWebView(View):
    """Post detail page with media viewer, engagement bar, and threaded comments."""
    template_name = 'posts/detail.html'

    def get(self, request, pk):
        post = get_object_or_404(
            Post.objects.select_related('author').prefetch_related('media', 'likes', 'comments__user', 'comments__replies__user'),
            pk=pk
        )
        is_liked = request.user.is_authenticated and post.likes.filter(user=request.user).exists()
        is_bookmarked = request.user.is_authenticated and post.bookmarks.filter(user=request.user).exists()
        comments = post.comments.filter(parent=None).order_by('-created_at')

        context = {
            'post': post,
            'is_liked': is_liked,
            'is_bookmarked': is_bookmarked,
            'comments': comments,
            'is_author': request.user.is_authenticated and request.user == post.author,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class PostEditWebView(View):
    """Edit post caption and location."""
    template_name = 'posts/edit.html'

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        return render(request, self.template_name, {'post': post})

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        caption = request.POST.get('caption', '')
        location = request.POST.get('location', '')

        try:
            PostService.update_post(post=post, user=request.user, caption=caption, location=location)
            messages.success(request, 'Post updated successfully.')
            return redirect('post-detail-web', pk=post.id)
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, self.template_name, {'post': post})


@method_decorator(login_required, name='dispatch')
class PostDeleteWebView(View):
    """Delete a post."""
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        try:
            PostService.delete_post(post=post, user=request.user)
            messages.success(request, 'Post has been removed.')
            return redirect('profile-me')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('post-detail-web', pk=pk)


@method_decorator(login_required, name='dispatch')
class PostLikeWebToggleView(View):
    """Handles like button click from web templates (supports async fetch & form redirect)."""
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        is_liked, likes_count = PostService.toggle_like(post=post, user=request.user)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'is_liked': is_liked, 'likes_count': likes_count})

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
        return redirect(next_url)


@method_decorator(login_required, name='dispatch')
class PostCommentWebCreateView(View):
    """Handles comment submission from web templates."""
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        text = request.POST.get('text', '')
        parent_id = request.POST.get('parent_id')

        try:
            CommentService.create_comment(
                post=post,
                user=request.user,
                text=text,
                parent_id=int(parent_id) if parent_id and parent_id.isdigit() else None
            )
            messages.success(request, 'Comment added.')
        except ValidationError as e:
            messages.error(request, str(e))

        next_url = request.POST.get('next') or f'/posts/{post.id}/'
        return redirect(next_url)
