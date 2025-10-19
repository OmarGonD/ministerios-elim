#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
sys.path.append('d:\web_proyects\ministerios-elim')
django.setup()

from django.contrib.auth.models import User
from pastores.models import UserProfile as PastorProfile
from miembros.models import MemberProfile

def check_users():
    users = User.objects.all()
    print('=== USUARIOS REGISTRADOS ===')
    for user in users:
        print(f'Usuario: {user.username} ({user.email})')

        # Verificar si tiene perfil de pastor
        try:
            pastor_profile = user.pastores_profile
            print(f'  - Perfil Pastor: {pastor_profile.role}')
        except Exception as e:
            print(f'  - Perfil Pastor: NO TIENE ({str(e)})')

        # Verificar si tiene perfil de miembro
        try:
            member_profile = user.member_profile
            print(f'  - Perfil Miembro: {member_profile.role}')
        except Exception as e:
            print(f'  - Perfil Miembro: NO TIENE ({str(e)})')

        print()

if __name__ == '__main__':
    check_users()
