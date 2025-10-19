from django import template

register = template.Library()

@register.filter
def email_prefix(email):
    """Extract the part before @ from an email address"""
    if email and '@' in email:
        return email.split('@')[0]
    return email
