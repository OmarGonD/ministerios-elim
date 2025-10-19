from django.db import models
from django.conf import settings
from wagtail.images.models import Image
from django_countries.fields import CountryField


class Iglesia(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='iglesias')
    nombre = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    
    # Nuevos campos de horarios con más detalle
    culto_oracion_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Culto de Oración')
    culto_oracion_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Culto de Oración')
    
    estudio_biblico_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Estudio Bíblico')
    estudio_biblico_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Estudio Bíblico')
    
    culto_general_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Culto General')
    culto_general_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Culto General')
    
    # Campos antiguos (mantener por compatibilidad)
    culto_oracion = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    estudio_biblico = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    culto_general = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    
    telefono = models.CharField(max_length=50, blank=True)
    country = CountryField(blank=True, null=True, help_text='País donde está ubicada la iglesia')
    foto = models.ForeignKey('wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Iglesia'
        verbose_name_plural = 'Iglesias'

    def __str__(self):
        return f"{self.nombre} ({self.owner})"

    def get_horarios_display(self):
        """Devuelve una lista de horarios formateados para mostrar"""
        horarios = []
        if self.culto_oracion_dia and self.culto_oracion_hora:
            periodo = 'a. m.' if self.culto_oracion_hora.hour < 12 else 'p. m.'
            hora_12 = self.culto_oracion_hora.hour % 12
            hora_12 = 12 if hora_12 == 0 else hora_12
            horarios.append(f"Culto de Oración: {self.culto_oracion_dia.title()} {hora_12}:{self.culto_oracion_hora.minute:02d} {periodo}")
        elif self.culto_oracion:
            horarios.append(f"Culto de Oración: {self.culto_oracion}")
            
        if self.estudio_biblico_dia and self.estudio_biblico_hora:
            periodo = 'a. m.' if self.estudio_biblico_hora.hour < 12 else 'p. m.'
            hora_12 = self.estudio_biblico_hora.hour % 12
            hora_12 = 12 if hora_12 == 0 else hora_12
            horarios.append(f"Estudio Bíblico: {self.estudio_biblico_dia.title()} {hora_12}:{self.estudio_biblico_hora.minute:02d} {periodo}")
        elif self.estudio_biblico:
            horarios.append(f"Estudio Bíblico: {self.estudio_biblico}")
            
        if self.culto_general_dia and self.culto_general_hora:
            periodo = 'a. m.' if self.culto_general_hora.hour < 12 else 'p. m.'
            hora_12 = self.culto_general_hora.hour % 12
            hora_12 = 12 if hora_12 == 0 else hora_12
            horarios.append(f"Culto General: {self.culto_general_dia.title()} {hora_12}:{self.culto_general_hora.minute:02d} {periodo}")
        elif self.culto_general:
            horarios.append(f"Culto General: {self.culto_general}")
            
        return horarios

    def save(self, *args, **kwargs):
        # Set default country from owner's profile if not set
        if not self.country and self.owner:
            if hasattr(self.owner, 'pastores_profile') and self.owner.pastores_profile.country:
                self.country = self.owner.pastores_profile.country
            elif hasattr(self.owner, 'member_profile') and self.owner.member_profile.country:
                self.country = self.owner.member_profile.country
        super().save(*args, **kwargs)
