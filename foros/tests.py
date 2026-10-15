from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.apps import apps
from django.urls import reverse


User = get_user_model()


class ForosSignalsTest(TestCase):
    def setUp(self):
        Forum = apps.get_model('foros', 'Forum')
        self.Topic = apps.get_model('foros', 'Topic')
        self.Post = apps.get_model('foros', 'Post')
        self.user = User.objects.create_user(username='tester', password='pass')
        self.forum = Forum.objects.create(title='General', description='General forum')

    def test_topics_api_and_posts_api_return_json(self):
        Topic = apps.get_model('foros', 'Topic')
        Post = apps.get_model('foros', 'Post')
        topic = Topic.objects.create(forum=self.forum, title='API Topic', created_by=self.user, is_published=True)
        Post.objects.create(topic=topic, body='Hello', created_by=self.user, is_public=True)
        client = self.client
        resp2 = client.get(f'/foros/{self.forum.pk}/api/topics/')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('topics', resp2.json())
        resp3 = client.get(f'/foros/{self.forum.pk}/api/topics/{topic.pk}/posts/')
        self.assertEqual(resp3.status_code, 200)
        self.assertIn('posts', resp3.json())

    @override_settings(ADMINS=(('Admin', 'admin@example.com'),))
    def test_topic_creation_sends_admin_email_when_not_published(self):
        mail.outbox = []
        topic = self.Topic.objects.create(forum=self.forum, title='Hello', created_by=self.user, is_published=False)
        # Signal should send email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nuevo tema pendiente', mail.outbox[0].subject)

    @override_settings(ADMINS=(('Admin', 'admin@example.com'),))
    def test_post_creation_sends_admin_email_when_not_public(self):
        topic = self.Topic.objects.create(forum=self.forum, title='Hello', created_by=self.user, is_published=True)
        mail.outbox = []
        post = self.Post.objects.create(topic=topic, body='Hi', created_by=self.user, is_public=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nuevo post pendiente', mail.outbox[0].subject)

    def test_moderation_report_and_post_only_vote(self):
        topic = self.Topic.objects.create(
            forum=self.forum, title='Tema visible', created_by=self.user, is_published=True
        )
        post = self.Post.objects.create(
            topic=topic, body='Respuesta visible', created_by=self.user, is_public=True
        )
        self.client.force_login(self.user)
        vote_url = reverse('foros:vote_post', args=[post.pk])
        self.assertEqual(self.client.get(vote_url).status_code, 405)
        self.assertEqual(self.client.post(vote_url).status_code, 200)
        report_url = reverse('foros:report_post', args=[post.pk])
        self.assertEqual(self.client.post(report_url, {'reason': 'Contenido inapropiado'}).status_code, 302)

        moderator = User.objects.create_user(username='moderator', password='pass', is_staff=True)
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name='Moderadores de foros')
        moderator.groups.add(group)
        self.client.force_login(moderator)
        dashboard = self.client.get(reverse('foros:moderation_dashboard'))
        self.assertContains(dashboard, 'Contenido inapropiado')

    def test_regular_user_topics_require_approval(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('foros:create_topic', args=[self.forum.pk]), {'title': 'Pregunta doctrinal'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.Topic.objects.get(title='Pregunta doctrinal').is_published)
        self.assertContains(response, 'pendiente de moderación')
