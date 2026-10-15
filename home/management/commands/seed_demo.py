"""Load repeatable example content without updating existing records."""
import json
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Site

from doctrina.models import (
    DoctrinaAvanzadaPage, DoctrinaBasicaPage, DoctrinaComment,
    DoctrinaDocument, DoctrinaEntryPage, DoctrinaIndexPage,
    DoctrinaIntermediaPage,
)
from foros.models import Comment, Forum, Post, Topic, Vote
from graficos_interactivos.models import GraficoInteractivo
from home.models import WhoWeArePage
from iglesias.models import (
    CityIndexPage, CountryIndexPage, IglesiaEventPage, IglesiaPage,
    PreachMaterial, Sermon,
)
from miembros.models import MemberProfile
from pastores.models import UserProfile


class Command(BaseCommand):
    help = 'Carga datos demo en todas las secciones, sin duplicar ni sobrescribir contenido'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='ElimDemo2026!',
                            help='Contraseña para las cuentas nuevas (no cambia cuentas existentes)')
        parser.add_argument('--refresh-doctrina', action='store_true',
                            help='Actualiza el texto lorem ipsum y las portadas de las entradas demo existentes')
        parser.add_argument('--refresh-images', action='store_true',
                            help='Actualiza las imágenes de las páginas y perfiles demo existentes')

    def image(self, slug):
        if slug not in self.demo_images:
            source = Path(settings.BASE_DIR) / 'static/img/demo' / f'{slug}.png'
            self.demo_images[slug] = self.resource(get_image_model(), f'Demo imagen: {slug}', source)
        return self.demo_images[slug]

    def refresh_page_images(self, page, **fields):
        if self.refresh_images and any(getattr(page, name) != value for name, value in fields.items()):
            for name, value in fields.items():
                setattr(page, name, value)
            page.save_revision().publish()

    def page(self, model, parent, slug, title, **defaults):
        existing = parent.get_children().filter(slug=slug).first()
        if existing:
            if not isinstance(existing.specific, model):
                raise CommandError(f'El slug {slug!r} ya pertenece a otro tipo de página.')
            return existing.specific, False
        page = parent.add_child(instance=model(
            slug=slug, title=title, show_in_menus=True, **defaults,
        ))
        page.save_revision().publish()
        return page, True

    def user(self, username, first_name, country, **profile_defaults):
        is_member = profile_defaults.pop('member', False)
        User = get_user_model()
        email = f'{username}@example.com'
        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email, 'first_name': first_name, 'last_name': 'Demo',
        })
        if user.email != email:
            raise CommandError(f'La cuenta {username!r} ya existe y no es una cuenta demo.')
        if created:
            user.set_password(self.password)
            user.save(update_fields=['password'])
            if is_member:
                MemberProfile.objects.filter(user=user).update(
                    country=country, **profile_defaults,
                )
            else:
                # The user signal creates a member profile; these accounts are pastors.
                MemberProfile.objects.filter(user=user).delete()
                UserProfile.objects.create(
                    user=user, country=country,
                    biography='<p>Perfil ficticio para explorar las funciones del sitio.</p>',
                    **profile_defaults,
                )
        elif self.refresh_images and 'foto' in profile_defaults:
            profile_model = MemberProfile if is_member else UserProfile
            profile_model.objects.filter(user=user).update(foto=profile_defaults['foto'])
        return user, created

    def resource(self, model, title, source):
        resource, _ = model.objects.get_or_create(title=title, defaults={
            'file': ContentFile(source.read_bytes(), name=source.name),
        })
        return resource

    @transaction.atomic
    def handle(self, *args, **options):
        self.password = options['password']
        self.refresh_images = options['refresh_images']
        self.demo_images = {}
        if not self.password:
            raise CommandError('La contraseña no puede estar vacía.')
        call_command('replace_homepage', stdout=self.stdout)
        home = Site.objects.get(is_default_site=True).root_page.specific
        fixtures = Path(settings.BASE_DIR) / 'home' / 'fixtures'
        cover = self.resource(get_image_model(), 'Demo: logo Ministerios Elim',
                              Path(settings.BASE_DIR) / 'static/img/logo-elim.png')
        # Assign the banner on initial setup; refreshing only changes image fields.
        if home.banner_image_id is None or self.refresh_images:
            banner = self.image('inicio')
            if home.banner_image_id != banner.pk:
                home.banner_image = banner
                home.save_revision().publish()
        notes = self.resource(get_document_model(), 'Demo: guía de estudio',
                              fixtures / 'demo-notas.txt')

        apostle_photo = self.image('jorge-fuentes')
        apostle_bio = (
            '<p>Desde 1996 ha estado al frente de esta casa con una sola misión: '
            'capacitar a los santos, con el fin de llegar a ser dignos de ver a '
            'nuestro amado Jesucristo en sus parusías.</p>'
        )
        apostle, apostle_created = self.user('demo_apostol', 'Jorge', 'PE', is_apostle=True,
                               foto=apostle_photo)
        if apostle_created or (apostle.first_name, apostle.last_name) == ('Samuel', 'Demo'):
            apostle.first_name = 'Jorge'
            apostle.last_name = 'Fuentes'
            apostle.save(update_fields=['first_name', 'last_name'])
        apostle_profile = apostle.pastores_profile
        if apostle_created or apostle_profile.biography == '<p>Perfil ficticio para explorar las funciones del sitio.</p>':
            apostle_profile.biography = apostle_bio
            apostle_profile.foto = apostle_photo
            apostle_profile.save(update_fields=['biography', 'foto'])
        supervisor, _ = self.user('demo_supervisor', 'Daniel', 'PE',
                                  is_superpastor=True, supervisor=apostle.pastores_profile,
                                  foto=self.image('supervisor'))
        member, member_created = self.user('demo_miembro', 'Ana', 'PE', member=True,
                             role='miembro', ocupacion='Docente', is_approved_member=True,
                             foto=self.image('miembro'))
        self.user('demo_visitante', 'Lucía', 'PE', member=True, role='visitante',
                  foto=self.image('visitante'))

        about, _ = self.page(WhoWeArePage, home, 'quienes-somos', 'Quiénes somos',
                  apostle_image=apostle_photo,
                  introduction_text='<p>Bienvenido a nuestra comunidad de fe y servicio. '
                                    'Esta página contiene información de demostración.</p>',
                  apostle_title='Apóstol Jorge Fuentes', apostle_subtitle='Máxima autoridad de Ministerios Elim',
                  apostle_bio=apostle_bio,
                  hierarchy_description='Equipo de ejemplo: apóstol, supervisor y pastores locales.')
        if about.apostle_title == 'Samuel Demo':
            about.apostle_title = 'Apóstol Jorge Fuentes'
            about.apostle_subtitle = 'Máxima autoridad de Ministerios Elim'
            about.apostle_bio = apostle_bio
            about.apostle_image = apostle_photo
            about.save_revision().publish()
        self.refresh_page_images(about, apostle_image=apostle_photo)
        index, _ = self.page(DoctrinaIndexPage, home, 'doctrina', 'Doctrina',
                             introduction='<p>Lecciones de ejemplo para conocer el sitio.</p>')
        # Reuse the existing graphic fixture by slug; do not load its fixed primary keys.
        graphics = []
        fixture = Path(settings.BASE_DIR) / 'graficos_interactivos/fixtures/initial_graficos.json'
        for item in json.loads(fixture.read_text()):
            fields = dict(item['fields'])
            slug = fields.pop('slug')
            fields.pop('created_at', None)
            fields.pop('updated_at', None)
            graphic, _ = GraficoInteractivo.objects.get_or_create(slug=slug, defaults=fields)
            graphics.append(graphic)

        levels = [
            (DoctrinaBasicaPage, 'basica', 'Doctrina Básica', [
                ('bautismo-en-agua', 'Bautismo en Agua', 'Mateo 28:19-20'),
                ('la-salvacion', 'La Salvación', 'Efesios 2:8-10'),
            ]),
            (DoctrinaIntermediaPage, 'intermedia', 'Doctrina Intermedia', [
                ('el-espiritu-santo', 'El Espíritu Santo', 'Hechos 2:1-4'),
                ('la-oracion', 'La oración y la vida cristiana', 'Mateo 6:9-13'),
            ]),
            (DoctrinaAvanzadaPage, 'avanzada', 'Doctrina Avanzada', [
                ('genealogia-de-jesus', 'Genealogía de Jesús', 'Mateo 1:1-17'),
                ('panorama-escatologico', 'Panorama escatológico', '1 Tesalonicenses 4:16-17'),
            ]),
        ]
        entries = []
        lorem_body = (fixtures / 'doctrina/lorem-ipsum.html').read_text()
        lorem_abstract = '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
        lorem_abstract += 'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>'
        for model, slug, title, lessons in levels:
            level_image = self.resource(
                get_image_model(), f'Demo doctrina: {lessons[0][1]}',
                fixtures / 'doctrina' / f'{lessons[0][0]}.png',
            )
            level, _ = self.page(model, index, slug, title,
                                 introduction='<p>Contenido de ejemplo para este nivel.</p>', image=level_image)
            self.refresh_page_images(level, image=level_image)
            for lesson_slug, lesson_title, reference in lessons:
                lesson_image = self.resource(
                    get_image_model(), f'Demo doctrina: {lesson_title}',
                    fixtures / 'doctrina' / f'{lesson_slug}.png',
                )
                entry, created = self.page(
                    DoctrinaEntryPage, level, lesson_slug, lesson_title,
                    subtitle='Lorem ipsum dolor sit amet', owner=apostle, created_by=apostle,
                    image=lesson_image, abstract=lorem_abstract, body=lorem_body,
                    references=f'<p>{reference}</p>',
                )
                if created:
                    if model is DoctrinaAvanzadaPage:
                        entry.graficos_embebidos.add(graphics[len(entries) % len(graphics)])
                    DoctrinaDocument.objects.create(page=entry, document=notes)
                    entry.save_revision().publish()
                elif entry.created_by_id == apostle.pk and (options['refresh_doctrina'] or self.refresh_images):
                    if options['refresh_doctrina']:
                        entry.subtitle = 'Lorem ipsum dolor sit amet'
                        entry.body = lorem_body
                        entry.abstract = lorem_abstract
                    entry.image = lesson_image
                    entry.save_revision().publish()
                entries.append(entry)
        DoctrinaComment.objects.get_or_create(
            page=entries[0], author=member,
            text='Comentario de ejemplo: esta lectura nos invita a poner la fe en práctica.',
        )

        churches = []
        locations = [
            ('PE', 'peru', 'Perú', 'lima', 'Lima', '-12.046374', '-77.042793', '+51 999 111 111'),
            ('PE', 'peru', 'Perú', 'arequipa', 'Arequipa', '-16.409047', '-71.537451', '+51 999 222 222'),
            ('ES', 'espana', 'España', 'madrid', 'Madrid', '40.416775', '-3.703790', '+34 600 333 333'),
        ]
        for country_code, country_slug, country_title, city_slug, city_title, latitude, longitude, phone in locations:
            country, _ = self.page(CountryIndexPage, home, country_slug, country_title,
                                   country=country_code)
            city, _ = self.page(CityIndexPage, country, city_slug, city_title,
                                introduction='Iglesias de ejemplo en esta ciudad.')
            pastor, pastor_created = self.user(
                f'demo_pastor_{city_slug}', f'Pastor {city_title}', country_code,
                supervisor=supervisor.pastores_profile,
                experiencia='Perfil pastoral de demostración.',
                foto=self.image(f'pastor-{city_slug}'),
            )
            church, _ = self.page(
                IglesiaPage, city, 'elim-demo', f'Elim {city_title} (Demo)', owner=pastor,
                address=f'Av. Ejemplo 123, {city_title} (dirección ficticia)',
                email=f'demo_{city_slug}@example.com', phone=phone, logo=cover,
                latitude=latitude, longitude=longitude, primary_language='es', is_verified=True,
                hero_image=self.image(f'iglesia-{city_slug}'),
                description='<p>Iglesia ficticia para explorar el directorio y el panel pastoral.</p>',
                worship_schedule='<p>Domingos: 10:00. Estudio bíblico: miércoles, 19:00.</p>',
            )
            demo_location_updates = {}
            if church.latitude is None:
                demo_location_updates['latitude'] = latitude
            if church.longitude is None:
                demo_location_updates['longitude'] = longitude
            if not church.phone:
                demo_location_updates['phone'] = phone
            if not church.is_verified:
                demo_location_updates['is_verified'] = True
            if demo_location_updates:
                for field, value in demo_location_updates.items():
                    setattr(church, field, value)
                church.save_revision().publish()
            self.refresh_page_images(church, hero_image=self.image(f'iglesia-{city_slug}'))
            if pastor_created:
                UserProfile.objects.filter(user=pastor).update(iglesia=church)
            churches.append(church)
            for offset, event_slug, event_title, category in [
                (7, 'encuentro-comunitario-demo', 'Encuentro comunitario (Demo)', 'general'),
                (14, 'reunion-jovenes-demo', 'Reunión de jóvenes (Demo)', 'jovenes'),
            ]:
                event_image = self.image('evento-jovenes' if category == 'jovenes' else 'evento-comunidad')
                event, _ = self.page(IglesiaEventPage, church, event_slug, event_title,
                          image=event_image,
                          date=timezone.now() + timedelta(days=offset), owner=pastor,
                          location='Auditorio de ejemplo', category=category,
                          description='<p>Evento ficticio: lectura, diálogo y actividades comunitarias.</p>')
                self.refresh_page_images(event, image=event_image)
            related_lesson = DoctrinaEntryPage.objects.live().filter(slug='la-salvacion').first()
            sermon, _ = Sermon.objects.get_or_create(
                iglesia=church, title='Video de ejemplo (Demo)', defaults={
                    'youtube_url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
                    'speaker': pastor.get_full_name() or 'Pastor Demo',
                    'topic': 'Salvación',
                    'series': 'Fundamentos de la fe',
                    'preached_at': timezone.localdate() - timedelta(days=7),
                    'related_doctrine': related_lesson,
                },
            )
            sermon_updates = {}
            for field, value in {
                'speaker': pastor.get_full_name() or 'Pastor Demo',
                'topic': 'Salvación',
                'series': 'Fundamentos de la fe',
                'preached_at': timezone.localdate() - timedelta(days=7),
                'related_doctrine': related_lesson,
            }.items():
                if not getattr(sermon, field):
                    sermon_updates[field] = value
            if sermon_updates:
                Sermon.objects.filter(pk=sermon.pk).update(**sermon_updates)
            material, created = PreachMaterial.objects.get_or_create(
                iglesia=church, title='La fe y el servicio (Demo)', defaults={
                    'category': 'salvacion', 'created_by': pastor,
                    'description': 'Presentación y guía de estudio de demostración.',
                },
            )
            if created:
                material.ppt_file.save('demo.pptx', ContentFile((fixtures / 'demo.pptx').read_bytes()), save=False)
                material.extra_file.save('demo-notas.txt', ContentFile((fixtures / 'demo-notas.txt').read_bytes()), save=False)
                material.save()
        # Assign only newly created demo members; retain later edits on repeat runs.
        if member_created:
            MemberProfile.objects.filter(user=member).update(iglesia=churches[0])

        for title, description, topic_title in [
            ('Demo: estudios bíblicos', 'Espacio de ejemplo para compartir lecturas.', '¿Cómo organizas tu estudio?'),
            ('Demo: comunidad', 'Espacio de ejemplo para el diálogo comunitario.', 'Bienvenidos a la comunidad demo'),
        ]:
            forum, _ = Forum.objects.get_or_create(title=title, defaults={'description': description})
            topic, _ = Topic.objects.get_or_create(forum=forum, title=topic_title, defaults={
                'created_by': apostle, 'is_published': True, 'is_pinned': True,
            })
            post, _ = Post.objects.get_or_create(topic=topic, body='Mensaje de demostración para iniciar la conversación.',
                                                 defaults={'created_by': apostle, 'is_public': True})
            Post.objects.get_or_create(topic=topic, body='Respuesta de ejemplo: gracias por compartir este espacio.',
                                       defaults={'created_by': member, 'is_public': True})
            Comment.objects.get_or_create(post=post, body='Comentario de demostración.', defaults={'created_by': member})
            Vote.objects.get_or_create(post=post, user=member)

        # Invalidate cached navigation after publishing new sections.
        transaction.on_commit(cache.clear)
        self.stdout.write(self.style.SUCCESS(
            'Datos demo cargados: quiénes somos, 3 niveles y 6 lecciones, 2 gráficos, '
            '3 iglesias, 6 eventos, 3 materiales, 2 foros y 7 cuentas.'
        ))
        self.stdout.write('Cuentas: demo_apostol, demo_supervisor, demo_pastor_lima, '
                          'demo_pastor_arequipa, demo_pastor_madrid, demo_miembro, demo_visitante.')
        if self.password == 'ElimDemo2026!':
            self.stdout.write('Contraseña para las cuentas nuevas: ElimDemo2026!')
        else:
            self.stdout.write('Las cuentas nuevas usan la contraseña indicada con --password.')
