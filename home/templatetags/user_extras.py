from django import template

register = template.Library()

@register.filter
def email_prefix(value):
    """Return the part of an email before the @, or the original value if no @."""
    try:
        return value.split('@', 1)[0]
    except Exception:
        return value

@register.filter
def hasattr(obj, attr_name):
    """Check if an object has a specific attribute."""
    try:
        return hasattr(obj, attr_name)
    except Exception:
        return False

@register.filter
def is_pastor(user):
    """Check if user is a pastor (pastor_elim or pastor_otro)."""
    try:
        if hasattr(user, 'pastores_profile'):
            return user.pastores_profile.role in ['pastor_elim', 'pastor_otro']
        return False
    except Exception:
        return False

@register.filter
def is_member(user):
    """Check if user is a member."""
    try:
        if hasattr(user, 'member_profile'):
            return user.member_profile.role == 'miembro'
        return False
    except Exception:
        return False
