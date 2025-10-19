from django.test import TestCase
from django.contrib.auth import get_user_model
from types import SimpleNamespace
from django.core.exceptions import PermissionDenied

from doctrina.wagtail_hooks import set_last_modified_by_on_publish
from doctrina.models import DoctrinaBasicaPage, DoctrinaEntryPage
from wagtail.models import Site, PageRevision


class PublishHookTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # create users
        self.u_elim = User.objects.create_user('test_pastor_elim', password='x')
        self.u_otro = User.objects.create_user('test_pastor_otro', password='x')

        # set roles via the UserProfile model and keep references
        from home.models import UserProfile
        self.profile_elim, _ = UserProfile.objects.get_or_create(user=self.u_elim)
        self.profile_elim.role = 'pastor_elim'
        self.profile_elim.save()
        self.profile_otro, _ = UserProfile.objects.get_or_create(user=self.u_otro)
        self.profile_otro.role = 'pastor_otro'
        self.profile_otro.save()

        # ensure a DoctrinaBasicaPage parent exists under the default site root
        site = Site.objects.get(is_default_site=True)
        root = site.root_page
        self.parent = DoctrinaBasicaPage(title='Test Doctrina Parent')
        root.add_child(instance=self.parent)

    def test_pastor_elim_allowed(self):
        entry = DoctrinaEntryPage(title='Entry allowed')
        self.parent.add_child(instance=entry)
        entry.body = 'body'
        entry.save()

    req = SimpleNamespace(user=self.u_elim)
    # attach profile so hook can read role reliably
    req.user.profile = self.profile_elim
    # Should not raise and should create a revision by this user
    set_last_modified_by_on_publish(req, entry)
    self.assertTrue(PageRevision.objects.filter(page=entry, user=self.u_elim).exists())

    def test_pastor_otro_blocked(self):
        entry = DoctrinaEntryPage(title='Entry blocked')
        self.parent.add_child(instance=entry)
        entry.body = 'body'
        entry.save()

        req = SimpleNamespace(user=self.u_otro)
        req.user.profile = self.profile_otro
        with self.assertRaises(PermissionDenied):
            set_last_modified_by_on_publish(req, entry)
