from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from wagtail.images.models import Image
from django.dispatch import receiver
from django.db.models.signals import post_save


class MemberProfile(models.Model):
    ROLE_MIEMBRO = 'miembro'
    ROLE_AYUDA = 'ayuda'
    ROLE_VISITANTE = 'visitante'
    ROLE_CHOICES = [
        (ROLE_MIEMBRO, 'Soy miembro de una iglesia (Elim u otra iglesia)'),
        (ROLE_AYUDA, 'Soy ayuda / supermiembro'),
        (ROLE_VISITANTE, 'Solo soy visitante'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='member_profile', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MIEMBRO)
    country = CountryField(blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ForeignKey('wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    # Información específica de miembros
    iglesia = models.ForeignKey('iglesias.IglesiaPage', on_delete=models.SET_NULL, null=True, blank=True, related_name='miembros', verbose_name="Iglesia Afiliada")
    is_approved_member = models.BooleanField(default=False, verbose_name="Miembro Aprobado", help_text="Indica si el pastor ha aprobado a este miembro.")
    iglesia_afiliada = models.CharField(max_length=255, blank=True, null=True, help_text='Nombre de la iglesia a la que pertenece (Legacy)')
    fecha_afiliacion = models.DateField(blank=True, null=True, help_text='Fecha de afiliación como miembro')
    estado_civil = models.CharField(max_length=20, choices=[
        ('soltero', 'Soltero/a'),
        ('casado', 'Casado/a'),
        ('divorciado', 'Divorciado/a'),
        ('viudo', 'Viudo/a'),
    ], blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    ocupacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Member Profile for {self.user} ({self.role})"

    @property
    def is_member(self):
        return self.role == self.ROLE_MIEMBRO

    @property
    def is_visitor(self):
        return self.role == self.ROLE_VISITANTE


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_member_profile(sender, instance, created, **kwargs):
    if created:
        # Solo crear perfil de miembro si no tiene perfil de pastor
        if not hasattr(instance, 'pastores_profile'):
            MemberProfile.objects.create(user=instance)
