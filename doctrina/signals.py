# doctrina/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import DoctrinaEntryPage
from django.contrib.auth import get_user_model

# Temporarily disabled signal to avoid conflicts with hooks
# @receiver(pre_save, sender=DoctrinaEntryPage)
# def set_created_by(sender, instance, **kwargs):
#     print(f"[DEBUG] pre_save signal: page={instance.title}, type={type(instance).__name__}, "
#           f"has_request={hasattr(instance, '_request')}, created_by={instance.created_by}, "
#           f"page_id={instance.id}")
#     # Skip if already set or not a new page
#     if not instance.id and not instance.created_by:
#         print(f"[DEBUG] Signal skipped: no user context available for new page {instance.title}")