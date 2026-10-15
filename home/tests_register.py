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
            'privacy_accepted': 'on',
        }
        resp = self.client.post(url, data, follow=True)
        # Should redirect to home on success
        self.assertEqual(resp.status_code, 200)
        # Without username_display, registration uses the email prefix.
        user = self.User.objects.filter(email='pastor_elim@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'pastor_elim')
        # Profile should have role set
        profile = getattr(user, 'pastores_profile', None)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.role, 'pastor_elim')

    def test_registration_requires_privacy_consent(self):
        response = self.client.post(reverse('register'), {
            'email': 'sin-consentimiento@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'role': 'visitante',
            'country': 'PE',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.User.objects.filter(email='sin-consentimiento@example.com').exists())
        self.assertContains(response, 'Debes aceptar la política de privacidad')
