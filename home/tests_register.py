from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class RegisterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_register_pastor_elim(self):
        url = reverse('register')
        data = {
            'username': 'pastor_elim@example.com',
            'email': 'pastor_elim@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'role': 'pastor_elim',
            'country': 'ES',
        }
        resp = self.client.post(url, data, follow=True)
        # Should redirect to home on success
        self.assertEqual(resp.status_code, 200)
        # User should exist
        user = self.User.objects.filter(username='pastor_elim@example.com').first()
        self.assertIsNotNone(user)
        # Profile should have role set
        profile = getattr(user, 'profile', None)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.role, 'pastor_elim')
