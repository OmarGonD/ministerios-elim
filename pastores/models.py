from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from wagtail.images.models import Image
from wagtail.fields import RichTextField
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
    
    # Hierarchy flags
    is_apostle = models.BooleanField(default=False, verbose_name="¿Es Apóstol?")
    is_superpastor = models.BooleanField(default=False, verbose_name="¿Es Pastor de Pastores (Superpastor)?")

    # Información específica de pastores
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='pastores_a_cargo', verbose_name="Supervisor (Apóstol/Pastor de Pastores)")
    iglesia = models.ForeignKey('iglesias.IglesiaPage', on_delete=models.SET_NULL, null=True, blank=True, related_name='pastores', verbose_name="Iglesia Asignada")
    iglesia_principal = models.CharField(max_length=255, blank=True, null=True, help_text='Nombre de la iglesia principal (Legacy)')
    titulo_academico = models.CharField(max_length=100, blank=True, null=True, help_text='Título académico/teológico')
    experiencia = models.TextField(blank=True, null=True, help_text='Experiencia ministerial')
    fecha_ordenacion = models.DateField(blank=True, null=True, help_text='Fecha de ordenación ministerial')
    biography = RichTextField("Biografía / Historia", blank=True, null=True, help_text="Historia del pastor, sus inicios y testimonio.")

    def __str__(self):
        return f"Pastor Profile for {self.user} ({self.role})"

    @property
    def is_pastor_elim(self):
        return self.role == self.ROLE_PASTOR

    @property
    def is_pastor_otro(self):
        return self.role == self.ROLE_PASTOR_OTRO

    @property
    def role_display(self):
        """Returns the hierarchical title if flags are set, otherwise the default role display."""
        if self.is_apostle:
            return "Apóstol Elim"
        if self.is_superpastor:
            return "Pastor de Pastores"
        return self.get_role_display()


@receiver(post_save, sender=UserProfile)
def manage_user_group(sender, instance, created, **kwargs):
    """
    Manage Django groups based on UserProfile role and flags:
    - pastor_elim → Pastores group + is_staff (for Wagtail admin)
    - is_apostle → Apostol group  
    - is_superpastor → Pastor de Pastores group
    """
    from django.contrib.auth.models import Group
    
    try:
        # Pastores group (for pastor_elim role)
        pastores_group, group_created = Group.objects.get_or_create(name='Pastores')
        if instance.role == UserProfile.ROLE_PASTOR:
            instance.user.groups.add(pastores_group)
            # Grant is_staff for Wagtail admin access
            if not instance.user.is_staff:
                instance.user.is_staff = True
                instance.user.save(update_fields=['is_staff'])
        else:
            instance.user.groups.remove(pastores_group)
        
        # Set up Wagtail page permissions for the Pastores group if newly created
        if group_created:
            try:
                from pastores.permissions import setup_pastor_group_permissions
                setup_pastor_group_permissions(pastores_group)
            except Exception:
                pass  # Permissions will be set up by management command instead
        
        # Apostol group (set only via is_apostle flag by superuser)
        apostol_group, _ = Group.objects.get_or_create(name='Apostol')
        if instance.is_apostle:
            instance.user.groups.add(apostol_group)
            # Apostles also need staff access
            if not instance.user.is_staff:
                instance.user.is_staff = True
                instance.user.save(update_fields=['is_staff'])
        else:
            instance.user.groups.remove(apostol_group)
        
        # Pastor de Pastores group (set via is_superpastor flag by Apostol)
        superpastor_group, _ = Group.objects.get_or_create(name='Pastor de Pastores')
        if instance.is_superpastor:
            instance.user.groups.add(superpastor_group)
            # Superpastores also need staff access
            if not instance.user.is_staff:
                instance.user.is_staff = True
                instance.user.save(update_fields=['is_staff'])
        else:
            instance.user.groups.remove(superpastor_group)
    except Exception:
        pass
