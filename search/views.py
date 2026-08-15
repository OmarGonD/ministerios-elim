from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse

from wagtail.models import Page

# To enable logging of search queries for use with the "Promoted search results" module
# <https://docs.wagtail.org/en/stable/reference/contrib/searchpromotions.html>
# uncomment the following line and the lines indicated in the search function
# (after adding wagtail.contrib.search_promotions to INSTALLED_APPS):

# from wagtail.contrib.search_promotions.models import Query


from django.http import JsonResponse
from wagtail.images.models import Image

def search(request):
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", 1)

    # Search
    if search_query:
        search_results = Page.objects.live().search(search_query)
    else:
        search_results = Page.objects.none()

    # Handle AJAX for instant search
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        results_data = []
        # Limit instant search to top 8 results
        for item in search_results[:8]:
            specific = item.specific
            img_url = None
            
            # Try to find an image in common locations
            image_obj = getattr(specific, 'image', None) or getattr(specific, 'foto', None)
            if image_obj and isinstance(image_obj, Image):
                # Using a small rendition for search results
                rendition = image_obj.get_rendition('fill-100x100')
                img_url = rendition.url
            
            # Determine a nice label for content type
            content_type = specific._meta.verbose_name.title()
            
            results_data.append({
                'title': item.title,
                'url': item.url,
                'content_type': content_type,
                'image': img_url,
                'description': getattr(specific, 'search_description', '') or getattr(specific, 'abstract', '')[:100]
            })
        return JsonResponse({'results': results_data})

    # Pagination for standard results page
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
        },
    )
