from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group

User = get_user_model()


class Command(BaseCommand):
    help = 'Grant superuser status to a user by username or email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user to make superuser',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to make superuser',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create a new superuser if user does not exist',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        create = options.get('create', False)

        if not username and not email:
            self.stdout.write(
                self.style.ERROR('You must provide either --username or --email')
            )
            return

        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(email=email)

            user.is_superuser = True
            user.is_staff = True
            user.save()

            # Grant Wagtail admin access permission
            try:
                wagtailadmin_content_type = ContentType.objects.get(
                    app_label="wagtailadmin", model="admin"
                )
                admin_permission = Permission.objects.get(
                    content_type=wagtailadmin_content_type,
                    codename="access_admin"
                )
                user.user_permissions.add(admin_permission)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stdout.write(
                    self.style.WARNING(
                        'Wagtail admin permission not found. This is normal if migrations haven\'t run.'
                    )
                )

            # Add user to Wagtail Editors group if it exists
            try:
                editors_group = Group.objects.get(name="Editors")
                user.groups.add(editors_group)
                self.stdout.write(
                    self.style.SUCCESS('Added user to Wagtail Editors group')
                )
            except Group.DoesNotExist:
                pass

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully granted superuser status to {user.username} ({user.email})'
                )
            )
        except User.DoesNotExist:
            if create:
                if not username:
                    username = email.split('@')[0] if email else 'admin'
                if not email:
                    email = f'{username}@example.com'

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    is_superuser=True,
                    is_staff=True,
                )

                # Grant Wagtail admin access permission
                try:
                    wagtailadmin_content_type = ContentType.objects.get(
                        app_label="wagtailadmin", model="admin"
                    )
                    admin_permission = Permission.objects.get(
                        content_type=wagtailadmin_content_type,
                        codename="access_admin"
                    )
                    user.user_permissions.add(admin_permission)
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    pass

                # Add user to Wagtail Editors group if it exists
                try:
                    editors_group = Group.objects.get(name="Editors")
                    user.groups.add(editors_group)
                except Group.DoesNotExist:
                    pass

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created superuser {user.username} ({user.email})'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'Note: You will need to set a password for this user. '
                        'You can do this in the Django admin or use: '
                        'python manage.py changepassword <username>'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'User not found. Use --create to create a new superuser.'
                    )
                )

