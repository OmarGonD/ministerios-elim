from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Page, Site

from home.models import HomePage


class ConfigureHomepageTests(TestCase):
    def test_configures_homepage_without_deleting_existing_content(self):
        site = Site.objects.get(is_default_site=True)
        original_page_id = site.root_page_id
        call_command('replace_homepage')
        site.refresh_from_db()
        self.assertIsInstance(site.root_page.specific, HomePage)
        self.assertTrue(Page.objects.filter(pk=original_page_id).exists())
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home_page.html')
        self.assertContains(response, 'Bienvenido a Ministerios Elim')

        page_count = Page.objects.count()
        homepage_id = site.root_page_id
        call_command('replace_homepage')
        site.refresh_from_db()
        self.assertEqual(Page.objects.count(), page_count)
        self.assertEqual(site.root_page_id, homepage_id)
