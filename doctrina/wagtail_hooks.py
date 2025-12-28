# doctrina/wagtail_hooks.py
from wagtail import hooks
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.utils.html import format_html


# ============================================================================
# ROLE-BASED PERMISSION HELPERS
# ============================================================================

# Groups that can edit ANY Doctrina entry and publish without approval
PRIVILEGED_GROUPS = {'Apostol', 'Pastor de Pastores'}


def user_can_edit_any_doctrina(user):
    """
    Check if user belongs to privileged groups (Apostol or Pastor de Pastores).
    These users can edit any Doctrina entry, not just ones they own.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=PRIVILEGED_GROUPS).exists()


def user_can_publish_doctrina(user):
    """
    Check if user can publish Doctrina pages.
    Superusers and privileged groups can publish.
    Regular Pastores can only publish pages they own.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=PRIVILEGED_GROUPS).exists()


# ============================================================================
# PERMISSION HOOKS
# ============================================================================

@hooks.register('before_edit_page')
def restrict_pastores_to_own_pages(request, page):
    """
    Restrict Pastores (non-privileged users) to editing only their own pages.
    Apostol and Pastor de Pastores can edit any page.
    """
    from .models import DoctrinaEntryPage
    
    if not isinstance(page, DoctrinaEntryPage):
        return  # Only apply to Doctrina entries
    
    if not request.user.is_authenticated:
        raise PermissionDenied("Debes iniciar sesión para editar.")
    
    # Privileged users can edit any page
    if user_can_edit_any_doctrina(request.user):
        print(f"[PERMISSION] {request.user.username} (privileged) allowed to edit page '{page.title}'")
        return
    
    # Pastores can only edit pages they own
    if page.owner != request.user:
        print(f"[PERMISSION] {request.user.username} blocked from editing page '{page.title}' (owner: {page.owner})")
        raise PermissionDenied("Solo puedes editar tus propias entradas de doctrina.")
    
    print(f"[PERMISSION] {request.user.username} allowed to edit own page '{page.title}'")


@hooks.register('before_publish_page')
def check_publish_permission(request, page):
    """
    Check publish permissions for Doctrina pages.
    - Superusers and privileged groups: Can publish any page
    - Pastores: Can only publish pages they own
    """
    from .models import DoctrinaEntryPage
    
    if not isinstance(page, DoctrinaEntryPage):
        return page  # Only apply to Doctrina entries
    
    if not request.user.is_authenticated:
        raise PermissionDenied("Debes iniciar sesión para publicar.")
    
    # Privileged users can publish any page
    if user_can_publish_doctrina(request.user):
        print(f"[PERMISSION] {request.user.username} (privileged) allowed to publish page '{page.title}'")
    else:
        # Pastores can only publish pages they own
        if page.owner != request.user:
            print(f"[PERMISSION] {request.user.username} blocked from publishing page '{page.title}' (owner: {page.owner})")
            raise PermissionDenied("Solo puedes publicar tus propias entradas de doctrina.")
        print(f"[PERMISSION] {request.user.username} allowed to publish own page '{page.title}'")
    
    # Update last_modified_by on publish
    with transaction.atomic():
        page.last_modified_by = request.user
        page.save_revision(user=request.user)
        print(f"[PERMISSION] Updated last_modified_by to {request.user.username} for page '{page.title}'")
    
    return page


# ============================================================================
# METADATA HOOKS
# ============================================================================

@hooks.register('construct_main_menu')
def test_hook_registration(request, menu_items):
    print(f"[DEBUG] construct_main_menu hook triggered: user={request.user}, authenticated={request.user.is_authenticated}")
    return menu_items


@hooks.register('before_save_page')
def set_created_and_modified_by(request, page, **kwargs):
    """Set created_by and last_modified_by fields on save."""
    from .models import DoctrinaEntryPage
    
    if isinstance(page, DoctrinaEntryPage) and request.user.is_authenticated:
        # Only set created_by if the page is being created (no ID yet)
        if not page.id:
            page.created_by = request.user
            print(f"[METADATA] Set created_by to {request.user.username} for new page '{page.title}'")
        # Always update last_modified_by
        page.last_modified_by = request.user
        print(f"[METADATA] Set last_modified_by to {request.user.username} for page '{page.title}'")
    return page


@hooks.register('after_publish_page')
def set_created_and_modified_by_after_publish(request, page):
    """Ensure metadata is set after publish."""
    from .models import DoctrinaEntryPage
    
    if isinstance(page, DoctrinaEntryPage) and request.user.is_authenticated:
        with transaction.atomic():
            updates = {'last_modified_by': request.user}
            page_obj = DoctrinaEntryPage.objects.get(id=page.id)
            if not page_obj.created_by:
                updates['created_by'] = request.user
                print(f"[METADATA] Set created_by to {request.user.username} after publish for '{page.title}'")
            DoctrinaEntryPage.objects.filter(id=page.id).update(**updates)
            print(f"[METADATA] Updated last_modified_by to {request.user.username} after publish for '{page.title}'")