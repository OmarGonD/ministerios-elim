from django.db import models
from django.urls import reverse
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver




### User Profile ###

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    second_name = models.CharField(max_length=50, blank=True, null=True)
    mother_last_name = models.CharField(max_length=30, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    dni = models.CharField(max_length=50, blank=True)
    passport = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True)
    shipping_address1 = models.CharField(max_length=100, blank=False)
    reference = models.CharField(max_length=100, blank=True, null=True)
    shipping_department = models.CharField(max_length=100, blank=False)
    shipping_province = models.CharField(max_length=100, blank=False)
    shipping_district = models.CharField(max_length=100, blank=False)
    #photo = models.ImageField(upload_to='profile_pics', default='profile_pics/default_profile_pic.png')
  

    def __str__(self):
        return str(self.user.first_name) + "'s profile"



@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        instance.profile.save()



#####################################################################
# Model con informacion sobre el costo de los despachos a provincia #
#####################################################################


class Peru(models.Model):
    departamento = models.CharField(max_length=100, blank=False)
    provincia = models.CharField(max_length=100, blank=False)
    distrito = models.CharField(max_length=100, blank=False)
    costo_despacho_con_recojo = models.IntegerField(default=15)
    costo_despacho_sin_recojo = models.IntegerField(default=15)
    dias_despacho = models.IntegerField(default=4)

    def __str__(self):
        return self.departamento + " - " + self.provincia + " - " + self.distrito + '-' + str(self.dias_despacho)