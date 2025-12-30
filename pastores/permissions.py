# pastores/permissions.py
"""
Helper functions for setting up Wagtail permissions for pastor groups.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def get_page_permission(permission_type):
    """
    Get the Django Permission object for a page permission type.
    permission_type: 'add', 'change' (edit), or 'publish'
    """
    from wagtail.models import get_default_page_content_type
    content_type = get_default_page_content_type()
    codename = f"{permission_type}_page"
    return Permission.objects.get(content_type=content_type, codename=codename)


def setup_pastor_group_permissions(group=None):
    """
    Set up Wagtail page permissions for the Pastores group.
    Creates GroupPagePermission entries for Doctrina, Iglesia, and Event pages.
    """
    from wagtail.models import GroupPagePermission, Page
    from doctrina.models import DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage
    from iglesias.models import IglesiaPage, IglesiaEventPage
    
    if group is None:
        group, _ = Group.objects.get_or_create(name='Pastores')
    
    # Permission types we want to grant to pastors
    # Wagtail 7 uses: add_page, change_page (was 'edit'), publish_page
    permission_types = ['add', 'change', 'publish']
    
    # Get permission objects
    permission_objects = {}
    for perm_type in permission_types:
        try:
            permission_objects[perm_type] = get_page_permission(perm_type)
        except Permission.DoesNotExist:
            print(f"Warning: Permission '{perm_type}_page' not found")
            continue
    
    # Doctrina parent pages - pastors can add children (DoctrinaEntryPage) to these
    doctrina_page_models = [DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage]
    
    permissions_created = []
    
    for PageModel in doctrina_page_models:
        pages = PageModel.objects.all()
        for page in pages:
            for perm_type, perm_obj in permission_objects.items():
                gpp, created = GroupPagePermission.objects.get_or_create(
                    group=group,
                    page=page,
                    permission=perm_obj
                )
                if created:
                    permissions_created.append(f"{perm_type} on {page.title}")
    
    # Iglesia pages - pastors should be able to edit their assigned church
    for page in IglesiaPage.objects.all():
        for perm_type, perm_obj in permission_objects.items():
            gpp, created = GroupPagePermission.objects.get_or_create(
                group=group,
                page=page,
                permission=perm_obj
            )
            if created:
                permissions_created.append(f"{perm_type} on {page.title}")
    
    # Grant Wagtail admin access permission
    try:
        wagtail_admin_permission = Permission.objects.get(
            codename='access_admin',
            content_type__app_label='wagtailadmin'
        )
        group.permissions.add(wagtail_admin_permission)
        permissions_created.append("access_admin (wagtail)")
    except Permission.DoesNotExist:
        # Wagtail admin permission doesn't exist yet
        pass
    
    return permissions_created


def ensure_pastor_demo_exists():
    """
    Ensure the pastor_demo user exists with proper profile and group membership.
    Returns the user and a status message.
    """
    from django.contrib.auth.models import User
    from pastores.models import UserProfile
    
    user, user_created = User.objects.get_or_create(
        username='pastor_demo',
        defaults={
            'email': 'pastor_demo@example.com',
            'first_name': 'Pastor',
            'last_name': 'Demo',
            'is_staff': True,  # Required for Wagtail admin access
        }
    )
    
    # Set a password if user was just created
    if user_created:
        user.set_password('PastorDemo123!')
        user.save()
    
    # Ensure is_staff is True (for Wagtail admin access)
    if not user.is_staff:
        user.is_staff = True
        user.save()
    
    # Create or update pastores_profile
    profile, profile_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': UserProfile.ROLE_PASTOR,
        }
    )
    
    # The signal in models.py should automatically add to Pastores group,
    # but let's ensure it
    pastores_group, _ = Group.objects.get_or_create(name='Pastores')
    user.groups.add(pastores_group)
    
    status = {
        'user_created': user_created,
        'profile_created': profile_created,
        'username': user.username,
        'email': user.email,
        'groups': list(user.groups.values_list('name', flat=True)),
    }
    
    return user, status
