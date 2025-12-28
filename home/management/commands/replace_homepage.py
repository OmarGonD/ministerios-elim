from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page, Site
from home.models import HomePage


class Command(BaseCommand):
    help = 'Replace the default Wagtail homepage with a HomePage instance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--title',
            type=str,
            default='Home',
            help='Title for the new HomePage (default: Home)',
        )
        parser.add_argument(
            '--slug',
            type=str,
            default='home',
            help='Slug for the new HomePage (default: home)',
        )

    def handle(self, *args, **options):
        title = options.get('title', 'Home')
        slug = options.get('slug', 'home')

        # Get the root page (ID 1)
        try:
            root_page = Page.objects.get(id=1)
        except Page.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Root page (ID 1) not found!')
            )
            return

        # Find existing homepage (usually ID 2, but check all children of root)
        existing_homepage = root_page.get_children().first()
        site = None
        
        if existing_homepage:
            self.stdout.write(
                f'Found existing homepage: "{existing_homepage.title}" (ID: {existing_homepage.id})'
            )
            
            # Get the site that uses this page as root
            site = Site.objects.filter(root_page=existing_homepage).first()
            
            # Delete the existing homepage
            self.stdout.write('Deleting existing homepage...')
            existing_homepage.delete()
            self.stdout.write(
                self.style.SUCCESS('Existing homepage deleted successfully')
            )
            
            # Refresh root page from database to get updated tree structure
            root_page.refresh_from_db()
        else:
            self.stdout.write('No existing homepage found under root')
            site = Site.objects.filter(is_default_site=True).first()

        # Get or create HomePage content type
        homepage_content_type, created = ContentType.objects.get_or_create(
            model="homepage",
            app_label="home"
        )

        # Create new HomePage using Wagtail's proper method
        self.stdout.write(f'Creating new HomePage with title "{title}"...')
        
        # Calculate the path for the new page
        root_path = root_page.path
        # Check if there are any existing children
        existing_children = root_page.get_children()
        if existing_children.exists():
            # Get the last child's path and increment
            last_child = existing_children.order_by('-path').first()
            last_path_num = int(last_child.path[-4:])
            new_path_num = last_path_num + 1
            new_path = f"{root_path}{str(new_path_num).zfill(4)}"
        else:
            # First child - use 0001
            new_path = f"{root_path}0001"
        
        # Create the HomePage with all required fields
        homepage = HomePage(
            title=title,
            slug=slug,
            content_type=homepage_content_type,
            path=new_path,
            depth=root_page.depth + 1,
            url_path=f"/{slug}/",
            numchild=0,
        )
        homepage.save()
        
        # Update root page's numchild
        root_page.numchild = root_page.get_children().count()
        root_page.save(update_fields=['numchild'])
        
        # Save and publish
        revision = homepage.save_revision()
        revision.publish()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created HomePage "{title}" (ID: {homepage.id})'
            )
        )

        # Update the site to point to the new homepage
        if site:
            site.root_page = homepage
            site.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated site "{site.hostname}" to use new HomePage as root'
                )
            )
        else:
            # Create a new site if none exists
            site = Site.objects.create(
                hostname="localhost",
                root_page=homepage,
                is_default_site=True
            )
            self.stdout.write(
                self.style.SUCCESS('Created new default site')
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\nHomePage replacement complete!'
                f'\n  Visit: http://127.0.0.1:8000/'
            )
        )

