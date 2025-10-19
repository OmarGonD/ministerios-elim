from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import mail_admins
from django.conf import settings
from .models import Topic, Post


@receiver(post_save, sender=Topic)
def notify_admin_new_topic(sender, instance, created, **kwargs):
    if created and not instance.is_published:
        subject = f"Nuevo tema pendiente en foros: {instance.title}"
        message = f"Un nuevo tema ha sido creado en el foro '{instance.forum.title}' por {instance.created_by}.\n\nTítulo: {instance.title}\nID: {instance.pk}\n"
        mail_admins(subject, message)


@receiver(post_save, sender=Post)
def notify_admin_new_post(sender, instance, created, **kwargs):
    if created and not instance.is_public:
        subject = f"Nuevo post pendiente en foros: {instance.topic.title}"
        message = f"Un nuevo post ha sido creado en el tema '{instance.topic.title}' por {instance.created_by}.\n\nPost ID: {instance.pk}\nContenido:\n{instance.body[:1000]}"
        mail_admins(subject, message)
