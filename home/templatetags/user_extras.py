from django import template
import builtins

register = template.Library()

# Use built-in hasattr explicitly to avoid shadowing
_hasattr = builtins.hasattr

@register.filter
def email_prefix(value):
    """Return the part of an email before the @, or the original value if no @."""
    try:
        return value.split('@', 1)[0]
    except Exception:
        return value

@register.filter(name='hasattr')
def has_attr_filter(obj, attr_name):
    """Check if an object has a specific attribute."""
    try:
        return _hasattr(obj, attr_name)
    except Exception:
        return False

@register.filter
def is_pastor(user):
    """Check if user is a pastor (pastor_elim or pastor_otro)."""
    try:
        if _hasattr(user, 'pastores_profile'):
            return user.pastores_profile.role in ['pastor_elim', 'pastor_otro']
        return False
    except Exception:
        return False

@register.filter
def is_member(user):
    """Check if user is a member."""
    try:
        if _hasattr(user, 'member_profile'):
            return user.member_profile.role == 'miembro'
        return False
    except Exception:
        return False

@register.filter
def is_apostle(user):
    """Check if user is an apostle."""
    try:
        if _hasattr(user, 'pastores_profile'):
            return user.pastores_profile.is_apostle
        return False
    except Exception:
        return False

@register.filter
def is_superpastor(user):
    """Check if user is a Pastor de Pastores (superpastor)."""
    try:
        if _hasattr(user, 'pastores_profile'):
            return user.pastores_profile.is_superpastor
        return False
    except Exception:
        return False

@register.filter
def is_pastor_elim(user):
    """Check if user is a Pastor Elim (not just any pastor)."""
    try:
        if _hasattr(user, 'pastores_profile'):
            return user.pastores_profile.role == 'pastor_elim'
        return False
    except Exception:
        return False

@register.simple_tag
def can_edit_doctrina(user, page):
    """Check if user can directly edit a Doctrina entry (owner or apostle)."""
    try:
        if not user.is_authenticated:
            return False
        # Apostles can edit any entry
        try:
            profile = user.pastores_profile
            if profile.is_apostle:
                return True
        except Exception:
            pass
        # Owner pastor can edit their own entry
        if page.owner == user:
            return True
        return False
    except Exception:
        return False

@register.filter
def reading_time(html_content):
    """Calculate minutes of reading time for a given HTML string."""
    if not html_content:
        return 1
    
    import re
    # Strip HTML tags
    text = re.sub('<[^<]+?>', '', str(html_content))
    # Count words
    words = len(re.findall(r'\w+', text))
    # Average reading speed: 200 words per minute
    minutes = round(words / 200)
    return max(1, minutes)
