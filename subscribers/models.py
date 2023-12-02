from django.db import models

# Create your models here.
class Subscriber(models.Model):
    
    email = models.CharField(max_length=100, blank=False, null=False, help_text='Ingresa tu correo')
    full_name = models.CharField(max_length=100, blank=False, null=False, help_text='Nombres y apellidos')

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Suscrito"
        verbose_name_plural = "Suscritos"
         