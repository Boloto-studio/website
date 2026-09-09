from django.test import TestCase
from django.urls import reverse

from base.models import ContactRequest


class PublicPageTests(TestCase):
	def test_public_routes_render(self):
		routes = [
			reverse('home'),
			reverse('studio'),
			reverse('donation'),
			reverse('contact'),
		]

		for route in routes:
			with self.subTest(route=route):
				response = self.client.get(route)
				self.assertEqual(response.status_code, 200)

	def test_contact_form_creates_request(self):
		response = self.client.post(
			reverse('contact'),
			{
				'name': 'Operator Doe',
				'email': 'operator@example.com',
				'message': 'Testing the secure comm link.',
			},
		)

		self.assertRedirects(response, f"{reverse('contact')}?submitted=1")
		self.assertEqual(ContactRequest.objects.count(), 1)
