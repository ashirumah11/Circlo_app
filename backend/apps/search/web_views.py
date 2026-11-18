from django.shortcuts import render
from django.views import View

from .services import SearchService


class ExploreWebView(View):
    """
    Renders the Explore page: a visual grid of trending & popular posts.
    """
    template_name = 'feed/explore.html'

    def get(self, request):
        viewer = request.user if request.user.is_authenticated else None
        posts = SearchService.get_explore_posts(viewer=viewer, limit=60)

        context = {
            'posts': posts,
        }
        return render(request, self.template_name, context)


class SearchWebView(View):
    """
    Renders the search page with accounts, hashtags, and posts.
    """
    template_name = 'search/results.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        viewer = request.user if request.user.is_authenticated else None
        results = SearchService.unified_search(query, viewer=viewer) if query else None

        context = {
            'query': query,
            'results': results,
        }
        return render(request, self.template_name, context)
