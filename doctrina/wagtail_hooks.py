# doctrina/wagtail_hooks.py
from wagtail import hooks
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.utils.html import format_html

@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS to Wagtail admin"""
    return format_html(
        '<link rel="stylesheet" href="{}?v={}">',
        static('css/wagtail_admin.css'),
        '20250827-03'
    )

@hooks.register('construct_main_menu')
def test_hook_registration(request, menu_items):
    print(f"[DEBUG] construct_main_menu hook triggered: user={request.user}, authenticated={request.user.is_authenticated}")
    return menu_items

@hooks.register('before_save_page')
def set_created_and_modified_by(request, page, **kwargs):
    from .models import DoctrinaEntryPage
    print(f"[DEBUG] before_save_page hook: page={page.title}, type={type(page).__name__}, "
          f"user={request.user}, authenticated={request.user.is_authenticated}, page_id={page.id}")
    if isinstance(page, DoctrinaEntryPage) and request.user.is_authenticated:
        # Only set created_by if the page is being created (no ID yet)
        if not page.id:
            page.created_by = request.user
            print(f"[DEBUG] Set created_by to {request.user.username} for page {page.title}")
        # Always update last_modified_by
        page.last_modified_by = request.user
        print(f"[DEBUG] Set last_modified_by to {request.user.username} for page {page.title}")
    else:
        print(f"[DEBUG] Skipped before_save: page_type={type(page).__name__}, authenticated={request.user.is_authenticated}")
    return page

@hooks.register('before_publish_page')
def set_last_modified_by_on_publish(request, page):
    from .models import DoctrinaEntryPage
    print(f"[DEBUG] before_publish_page hook: page={page.title}, type={type(page).__name__}, "
          f"user={request.user}, authenticated={request.user.is_authenticated}")
    if isinstance(page, DoctrinaEntryPage) and request.user.is_authenticated:
        # Allow superusers or users with profile.role == 'pastor_elim' to publish doctrina pages
        if request.user.is_superuser:
            print(f"[DEBUG] Superuser allowed to publish: user={request.user}")
        else:
            try:
                role = getattr(request.user, 'profile', None)
                user_role = role.role if role is not None else None
            except Exception:
                user_role = None
            # Only allow pastors from Elim to publish; pastors from other ministries cannot publish here
            allowed_pastor_values = {'pastor_elim'}
            if user_role not in allowed_pastor_values:
                print(f"[DEBUG] Publish blocked: user={request.user} role={user_role}")
                raise PermissionDenied("Solo los pastores de Elim pueden publicar en esta sección.")
        with transaction.atomic():
            page.last_modified_by = request.user
            page.save_revision(user=request.user)
            print(f"[DEBUG] Set and saved last_modified_by to {request.user.username} on publish for {page.title}")
    else:
        print(f"[DEBUG] Skipped before_publish: page_type={type(page).__name__}, authenticated={request.user.is_authenticated}")
    return page

@hooks.register('after_publish_page')
def set_created_and_modified_by_after_publish(request, page):
    from .models import DoctrinaEntryPage
    print(f"[DEBUG] after_publish_page hook: page={page.title}, type={type(page).__name__}, "
          f"user={request.user}, authenticated={request.user.is_authenticated}, page_id={page.id}")
    if isinstance(page, DoctrinaEntryPage) and request.user.is_authenticated:
        with transaction.atomic():
            updates = {'last_modified_by': request.user}
            page_obj = DoctrinaEntryPage.objects.get(id=page.id)
            if not page_obj.created_by:
                updates['created_by'] = request.user
                print(f"[DEBUG] Set created_by to {request.user.username} after publish for {page.title}")
            DoctrinaEntryPage.objects.filter(id=page.id).update(**updates)
            print(f"[DEBUG] Directly updated last_modified_by to {request.user.username} after publish for {page.title}")
    else:
        print(f"[DEBUG] Skipped after_publish: page_type={type(page).__name__}, authenticated={request.user.is_authenticated}")