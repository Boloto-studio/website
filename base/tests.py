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


class SidebarSessionTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='mavka', password='secret123')

	def test_signed_out_sidebar_has_log_in_and_register(self):
		response = self.client.get(reverse('studio'))

		self.assertContains(response, f"{reverse('frogs-login')}?next={reverse('studio')}")
		self.assertContains(response, reverse('frogs-register'))
		self.assertNotContains(response, reverse('frogs-logout'))

	def test_log_in_returns_to_the_page_you_were_on(self):
		response = self.client.post(
			f"{reverse('frogs-login')}?next={reverse('studio')}",
			{'username': 'mavka', 'password': 'secret123'},
		)
		self.assertRedirects(response, reverse('studio'), fetch_redirect_response=False)

	def test_signed_in_sidebar_shows_user_and_log_out(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse('studio'))

		self.assertContains(response, 'mavka')
		self.assertContains(response, f'action="{reverse("frogs-logout")}"')
		self.assertNotContains(response, f"{reverse('frogs-login')}?next=")

	def test_log_out_needs_post(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get(reverse('frogs-logout')).status_code, 405)

		response = self.client.post(reverse('frogs-logout'))
		self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
		self.assertNotIn('_auth_user_id', self.client.session)
