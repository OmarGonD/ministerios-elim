from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'List all users in the system'

    def handle(self, *args, **options):
        users = User.objects.all().order_by('username')
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in the system.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nFound {users.count()} user(s):\n'))
        
        for user in users:
            status = []
            if user.is_superuser:
                status.append('SUPERUSER')
            if user.is_staff:
                status.append('STAFF')
            status_str = ', '.join(status) if status else 'Regular user'
            
            self.stdout.write(
                f'  Username: {self.style.SUCCESS(user.username)}'
            )
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Status: {status_str}')
            self.stdout.write('')

