from io import StringIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.models import Page, Site
from wagtail.images import get_image_model

from doctrina.models import DoctrinaEntryPage, DoctrinaProgress
from foros.models import Forum, Topic, Post
from graficos_interactivos.models import GraficoInteractivo
from home.models import WhoWeArePage, EngagementMetric
from iglesias.models import IglesiaPage, IglesiaEventPage, PreachMaterial, Sermon
from miembros.models import MemberProfile
from pastores.models import UserProfile


class SeedDemoTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        override = override_settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)
        call_command('seed_demo', stdout=StringIO())

    def test_populates_sections_and_downloads(self):
        self.assertEqual(DoctrinaEntryPage.objects.count(), 6)
        self.assertEqual(DoctrinaEntryPage.objects.values('image_id').distinct().count(), 6)
        for entry in DoctrinaEntryPage.objects.all():
            self.assertIn('Lorem ipsum dolor sit amet', entry.body)
            self.assertTrue(entry.image.title.startswith('Demo doctrina:'))
        self.assertEqual(IglesiaPage.objects.count(), 3)
        self.assertEqual(IglesiaEventPage.objects.count(), 6)
        self.assertEqual(PreachMaterial.objects.count(), 3)
        self.assertEqual(GraficoInteractivo.objects.count(), 2)
        self.assertEqual(Forum.objects.count(), 2)
        self.assertEqual(UserProfile.objects.count(), 5)
        self.assertEqual(MemberProfile.objects.count(), 2)
        self.assertFalse(UserProfile.objects.filter(foto__isnull=True).exists())
        self.assertFalse(MemberProfile.objects.filter(foto__isnull=True).exists())
        self.assertFalse(IglesiaEventPage.objects.filter(image__isnull=True).exists())
        self.assertTrue(WhoWeArePage.objects.get().apostle_image)
        for church in IglesiaPage.objects.all():
            self.assertEqual(church.logo.title, 'Demo: logo Ministerios Elim')
            self.assertNotEqual(church.hero_image_id, church.logo_id)
        self.assertTrue(self.client.login(username='demo_miembro', password='ElimDemo2026!'))
        self.client.logout()
        home = Site.objects.get(is_default_site=True).root_page
        paths = ['/', '/quienes-somos/', '/doctrina/', '/iglesias/', '/iglesias/materiales/', '/foros/']
        paths += [page.url for page in Page.objects.live().descendant_of(home).specific()]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.client.force_login(get_user_model().objects.get(username='demo_miembro'),
                                backend='django.contrib.auth.backends.ModelBackend')
        for material in PreachMaterial.objects.all():
            self.assertEqual(self.client.get(f'/iglesias/material/{material.pk}/').status_code, 200)
            with material.ppt_file.open('rb') as file, ZipFile(file) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('ppt/slides/slide1.xml', archive.namelist())
            with material.extra_file.open('rb') as file:
                self.assertIn('demostración', file.read().decode())
        for forum in Forum.objects.all():
            self.assertEqual(self.client.get(f'/foros/{forum.pk}/').status_code, 200)
            for topic in forum.topics.all():
                self.assertEqual(self.client.get(f'/foros/{forum.pk}/topics/{topic.pk}/').status_code, 200)

        for username, paths in [
            ('demo_miembro', ['/miembros/profile/', '/miembros/dashboard/']),
            ('demo_visitante', ['/miembros/dashboard/']),
            ('demo_pastor_lima', ['/profile/', '/iglesias/panel/', '/iglesias/mi-iglesia/']),
            ('demo_apostol', ['/iglesias/apostol/']),
        ]:
            self.client.force_login(get_user_model().objects.get(username=username),
                                    backend='django.contrib.auth.backends.ModelBackend')
            for path in paths:
                with self.subTest(username=username, path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)

    def test_repeat_preserves_content_passwords_and_counts(self):
        models = [Page, get_user_model(), UserProfile, MemberProfile,
                  GraficoInteractivo, Forum, Topic, Post, PreachMaterial, get_image_model()]
        counts = {model: model.objects.count() for model in models}
        page = WhoWeArePage.objects.get()
        page.introduction_text = '<p>Texto editado por el usuario.</p>'
        page.save()
        user = get_user_model().objects.get(username='demo_miembro')
        user.set_password('NuevaClave2026!')
        user.save()
        entry = DoctrinaEntryPage.objects.get(slug='la-salvacion')
        entry.body = '<p>Lección editada por el usuario.</p>'
        entry.save()
        church = IglesiaPage.objects.first()
        church.hero_image = church.logo
        church.save()
        other_entry = DoctrinaEntryPage.objects.get(slug='la-oracion')
        other_entry.created_by = user
        other_entry.body = '<p>Contenido de otro autor.</p>'
        other_entry.save()
        call_command('seed_demo', password='OtraClave2026!', stdout=StringIO())
        self.assertEqual({model: model.objects.count() for model in models}, counts)
        page.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(page.introduction_text, '<p>Texto editado por el usuario.</p>')
        self.assertTrue(user.check_password('NuevaClave2026!'))
        entry.refresh_from_db()
        self.assertEqual(entry.body, '<p>Lección editada por el usuario.</p>')
        church.refresh_from_db()
        self.assertEqual(church.hero_image_id, church.logo_id)

        call_command('demo_seed', refresh_images=True, stdout=StringIO())
        church.refresh_from_db()
        entry.refresh_from_db()
        page.refresh_from_db()
        user.refresh_from_db()
        self.assertNotEqual(church.hero_image_id, church.logo_id)
        self.assertEqual(church.logo.title, 'Demo: logo Ministerios Elim')
        self.assertEqual(entry.body, '<p>Lección editada por el usuario.</p>')
        self.assertEqual(page.introduction_text, '<p>Texto editado por el usuario.</p>')
        self.assertTrue(user.check_password('NuevaClave2026!'))

        call_command('seed_demo', refresh_doctrina=True, stdout=StringIO())
        entry.refresh_from_db()
        other_entry.refresh_from_db()
        self.assertIn('Lorem ipsum dolor sit amet', entry.body)
        self.assertEqual(other_entry.body, '<p>Contenido de otro autor.</p>')
        self.assertEqual({model: model.objects.count() for model in models}, counts)

    def test_primary_visitor_routes_are_visible(self):
        response = self.client.get('/')
        self.assertContains(response, 'Encuentra una iglesia')
        self.assertContains(response, 'Quiero aprender')
        self.assertContains(response, 'Quiero participar')

    def test_church_finder_searches_and_exposes_map_data(self):
        response = self.client.get('/iglesias/', {'q': 'Madrid', 'language': 'es'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Elim Madrid (Demo)')
        self.assertNotContains(response, 'Elim Lima (Demo)')
        self.assertContains(response, 'church-map-data')
        self.assertContains(response, 'Verificada')

    def test_member_can_save_doctrine_progress(self):
        user = get_user_model().objects.get(username='demo_miembro')
        entry = DoctrinaEntryPage.objects.get(slug='bautismo-en-agua')
        self.client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')
        response = self.client.post(f'/doctrina/progreso/{entry.pk}/')
        self.assertRedirects(response, entry.url)
        self.assertTrue(DoctrinaProgress.objects.filter(user=user, page=entry).exists())
        response = self.client.get(entry.url)
        self.assertContains(response, '50% de este nivel completado')
        self.assertContains(response, 'Siguiente lección')

    def test_events_sermons_and_role_dashboards(self):
        response = self.client.get('/iglesias/eventos/', {'category': 'jovenes'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reunión de jóvenes')

        sermon = Sermon.objects.select_related('related_doctrine').first()
        self.assertIsNotNone(sermon.related_doctrine)
        response = self.client.get('/iglesias/predicaciones/', {
            'speaker': sermon.speaker,
            'topic': sermon.topic,
            'series': sermon.series,
            'church': sermon.iglesia_id,
        })
        self.assertContains(response, sermon.title)
        self.assertContains(response, 'Doctrina relacionada')

        expectations = [
            ('demo_visitante', 'Visitante'),
            ('demo_miembro', 'Progreso de doctrina'),
            ('demo_pastor_lima', 'Panel Pastoral'),
            ('demo_supervisor', 'Panel de supervisión'),
            ('demo_apostol', 'Panel de liderazgo general'),
        ]
        for username, expected in expectations:
            self.client.force_login(get_user_model().objects.get(username=username))
            with self.subTest(username=username):
                response = self.client.get('/miembros/dashboard/', follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)

    def test_global_search_seo_and_private_metrics(self):
        response = self.client.get('/search/', {'query': 'Salvación'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Búsqueda global')
        self.assertContains(response, 'Predicación')
        self.assertTrue(EngagementMetric.objects.filter(event_type='search', label='all').exists())
        self.assertFalse(EngagementMetric.objects.filter(label__icontains='salvación').exists())

        for path, content in [
            ('/sitemap.xml', b'<?xml'),
            ('/robots.txt', b'Sitemap:'),
            ('/privacidad/', 'Datos que tratamos'.encode()),
        ]:
            with self.subTest(path=path):
                result = self.client.get(path)
                self.assertEqual(result.status_code, 200)
                self.assertIn(content, result.content)

        church = IglesiaPage.objects.first()
        self.client.get(church.url)
        self.assertTrue(EngagementMetric.objects.filter(
            event_type='church_view', label=church.title
        ).exists())
