from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Page, Site

from home.models import HomePage


class Command(BaseCommand):
    help = 'Configure the default site to use a HomePage without deleting pages'

    def add_arguments(self, parser):
        parser.add_argument('--title', default='Ministerios Elim')
        parser.add_argument('--slug', default='home')

    @transaction.atomic
    def handle(self, *args, **options):
        site = Site.objects.filter(is_default_site=True).first()
        if site and isinstance(site.root_page.specific, HomePage):
            self.stdout.write(self.style.SUCCESS('La portada de Ministerios Elim ya está configurada.'))
            return

        parent = site.root_page.get_parent() if site else Page.get_first_root_node()
        if parent is None:
            raise CommandError('No se encontró una página raíz donde crear la portada.')

        homepage = HomePage.objects.child_of(parent).first()
        if homepage is None:
            slug = options['slug']
            suffix = 2
            while parent.get_children().filter(slug=slug).exists():
                slug = f"{options['slug']}-{suffix}"
                suffix += 1
            homepage = parent.add_child(instance=HomePage(
                title=options['title'], slug=slug,
            ))
            homepage.save_revision().publish()
        elif not homepage.live:
            homepage.save_revision().publish()

        if site:
            site.root_page = homepage
            site.save(update_fields=['root_page'])
        else:
            Site.objects.create(
                hostname='localhost', root_page=homepage, is_default_site=True,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Portada configurada: {homepage.title}. Las páginas existentes se conservaron.'
        ))
