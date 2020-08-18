from django.test import TestCase, Client

from posts.models import User


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test", password="testpassword12345", email="test@yandex.ru")

    def test_profile(self):
        response = self.client.get(f"/{self.user}/")
        self.assertEqual(response.status_code, 200)  # Check if new user profile page exists
