from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from wagtail.images.models import Image
from django.dispatch import receiver
from django.db.models.signals import post_save


class UserProfile(models.Model):
    ROLE_PASTOR = 'pastor_elim'
    ROLE_PASTOR_OTRO = 'pastor_otro'
    ROLE_CHOICES = [
        (ROLE_PASTOR, 'Soy pastor Elim'),
        (ROLE_PASTOR_OTRO, 'Soy pastor - otro ministerio o independiente'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='pastores_profile', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PASTOR)
    country = CountryField(blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ForeignKey('wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    # Información específica de pastores
    iglesia_principal = models.CharField(max_length=255, blank=True, null=True, help_text='Nombre de la iglesia principal')
    titulo_academico = models.CharField(max_length=100, blank=True, null=True, help_text='Título académico/teológico')
    experiencia = models.TextField(blank=True, null=True, help_text='Experiencia ministerial')
    fecha_ordenacion = models.DateField(blank=True, null=True, help_text='Fecha de ordenación ministerial')

    def __str__(self):
        return f"Pastor Profile for {self.user} ({self.role})"

    @property
    def is_pastor_elim(self):
        return self.role == self.ROLE_PASTOR

    @property
    def is_pastor_otro(self):
        return self.role == self.ROLE_PASTOR_OTRO


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Solo crear perfil de pastor si el usuario es pastor
        # Esto se manejará desde las vistas/formularios de registro
        pass
