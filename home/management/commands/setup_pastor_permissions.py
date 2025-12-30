# home/management/commands/setup_pastor_permissions.py
"""
Management command to set up Wagtail permissions for the Pastores group.
This ensures pastors can create/edit entries in Doctrina, Iglesias, and Events.

Usage:
    python manage.py setup_pastor_permissions
    python manage.py setup_pastor_permissions --create-demo-user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Set up Wagtail page permissions for the Pastores group'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-demo-user',
            action='store_true',
            help='Also create/update the pastor_demo user',
        )

    def handle(self, *args, **options):
        from pastores.permissions import setup_pastor_group_permissions, ensure_pastor_demo_exists
        
        self.stdout.write(self.style.NOTICE('Setting up Pastores group permissions...'))
        
        # Ensure groups exist
        pastores_group, created = Group.objects.get_or_create(name='Pastores')
        if created:
            self.stdout.write(self.style.SUCCESS('  Created "Pastores" group'))
        else:
            self.stdout.write('  "Pastores" group already exists')
        
        # Set up page permissions
        permissions_created = setup_pastor_group_permissions(pastores_group)
        
        if permissions_created:
            self.stdout.write(self.style.SUCCESS(f'  Created {len(permissions_created)} permissions:'))
            for perm in permissions_created[:10]:  # Show first 10
                self.stdout.write(f'    - {perm}')
            if len(permissions_created) > 10:
                self.stdout.write(f'    ... and {len(permissions_created) - 10} more')
        else:
            self.stdout.write('  All permissions already exist')
        
        # Optionally create demo user
        if options['create_demo_user']:
            self.stdout.write(self.style.NOTICE('\nSetting up pastor_demo user...'))
            user, status = ensure_pastor_demo_exists()
            
            if status['user_created']:
                self.stdout.write(self.style.SUCCESS(f'  Created user: {status["username"]}'))
                self.stdout.write(f'    Email: {status["email"]}')
                self.stdout.write(f'    Default password: PastorDemo123!')
            else:
                self.stdout.write(f'  User already exists: {status["username"]}')
            
            if status['profile_created']:
                self.stdout.write(self.style.SUCCESS('  Created pastores_profile'))
            else:
                self.stdout.write('  pastores_profile already exists')
            
            self.stdout.write(f'  Groups: {", ".join(status["groups"])}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Pastor permissions setup complete!'))
