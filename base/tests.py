from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import BlogPost, ContactRequest


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

	def test_donation_page_uses_mockup_content(self):
		response = self.client.get(reverse('donation'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Support Protocol Initiated')
		self.assertContains(response, 'Maintenance Funds')
		self.assertContains(response, '80%')
		self.assertContains(response, 'TARGET: $500/MO')

	def test_blog_post_detail_renders_html_content(self):
		post = BlogPost.objects.create(
			title='Sector 7 Overhaul',
			content='**Kernel update**\n\nAttention all operatives.',
			published_date=timezone.now(),
		)

		response = self.client.get(reverse('blog_post', args=[post.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Sector 7 Overhaul')
		self.assertContains(response, 'Kernel update')
		self.assertContains(response, 'Attention all operatives.')

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
