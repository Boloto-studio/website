from unittest import mock

import stripe
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import BlogPost, ContactRequest


class PublicPageTests(TestCase):
	@mock.patch('base.views.stripe.Product.search', side_effect=stripe.error.APIConnectionError('offline'))
	@mock.patch('base.views.stripe.PaymentIntent.list', side_effect=stripe.error.APIConnectionError('offline'))
	def test_public_routes_render(self, _payment_list, _product_search):
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

	def _fake_payments(self, *payments):
		listing = mock.Mock()
		listing.auto_paging_iter.return_value = [
			mock.Mock(amount=amount, status=status) for amount, status in payments
		]
		return listing

	@mock.patch('base.views.stripe.Product.search', side_effect=stripe.error.APIConnectionError('offline'))
	@mock.patch('base.views.stripe.PaymentIntent.list')
	def test_donation_page_shows_progress_from_stripe(self, payment_list, _product_search):
		# $400 of the $500 target arrived; the failed $100 attempt doesn't count.
		payment_list.return_value = self._fake_payments(
			(25000, 'succeeded'), (15000, 'succeeded'), (10000, 'requires_payment_method'),
		)
		response = self.client.get(reverse('donation'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Support Protocol Initiated')
		self.assertContains(response, 'Maintenance Funds')
		self.assertContains(response, '80%')
		self.assertContains(response, '[████████░░]')
		self.assertContains(response, 'TARGET: $500/MO')
		self.assertEqual(response.context['donations_count'], 2)

	@mock.patch('base.views.stripe.Product.search', side_effect=stripe.error.APIConnectionError('offline'))
	@mock.patch('base.views.stripe.PaymentIntent.list', side_effect=stripe.error.APIConnectionError('offline'))
	def test_donation_page_survives_stripe_outage(self, _payment_list, _product_search):
		response = self.client.get(reverse('donation'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '0%')
		self.assertContains(response, '[░░░░░░░░░░]')

	def test_blog_post_detail_renders_html_content(self):
		author = User.objects.create_user(username='hq', password='secret123')
		post = BlogPost.objects.create(
			author=author,
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
