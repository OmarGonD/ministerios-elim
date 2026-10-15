from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from wagtail.models import Site

from doctrina.models import DoctrinaBasicaPage, DoctrinaEntryPage
from doctrina.wagtail_hooks import check_publish_permission


class PublishHookTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('owner', password='x')
        self.other = User.objects.create_user('other', password='x')
        self.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', password='x'
        )
        root = Site.objects.get(is_default_site=True).root_page
        self.parent = DoctrinaBasicaPage(title='Test Doctrina Parent')
        root.add_child(instance=self.parent)
        self.entry = DoctrinaEntryPage(
            title='Entry', body='body', owner=self.owner
        )
        self.parent.add_child(instance=self.entry)

    def test_owner_allowed(self):
        check_publish_permission(SimpleNamespace(user=self.owner), self.entry)
        revision = self.entry.get_latest_revision()
        self.assertEqual(revision.user, self.owner)
        self.assertEqual(revision.as_object().last_modified_by, self.owner)

    def test_other_user_blocked(self):
        with self.assertRaises(PermissionDenied):
            check_publish_permission(SimpleNamespace(user=self.other), self.entry)
        self.assertFalse(self.entry.revisions.filter(user=self.other).exists())

    def test_superuser_allowed_to_publish_another_users_page(self):
        check_publish_permission(SimpleNamespace(user=self.admin), self.entry)
        revision = self.entry.get_latest_revision()
        self.assertEqual(revision.user, self.admin)
        self.assertEqual(revision.as_object().last_modified_by, self.admin)
