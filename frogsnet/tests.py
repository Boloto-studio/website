from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import FrogProfileEditForm, WallPostForm
from .models import Frog, ForumPost


class FrogProfileEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='frogger',
            password='secret123',
            first_name='Frog',
            email='frogger@example.com',
        )
        self.frog = self.user.frog
        self.frog.bio = 'Old bio'
        self.frog.location = 'Old node'
        self.frog.minecraft_username = 'OldMine'
        self.frog.show_real_name = False
        self.frog.save()

    def test_profile_edit_form_updates_model_fields(self):
        form = FrogProfileEditForm(
            data={
                'username': 'frogger-updated',
                'first_name': 'Frog Updated',
                'bio': 'Updated bio',
                'minecraft_username': 'UpdatedMine',
                'location': 'SwampNode-East-04',
                'show_real_name': 'public',
                'show_active_modpacks': 'on',
                'show_last_played_server': 'on',
                'allow_friend_requests': 'on',
                'show_achievements': 'on',
                'allow_external_wall_posts': 'on',
            },
            instance=self.user,
            frog=self.frog,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.user.refresh_from_db()
        self.frog.refresh_from_db()
        self.assertEqual(self.user.username, 'frogger-updated')
        self.assertEqual(self.user.first_name, 'Frog Updated')
        self.assertEqual(self.frog.bio, 'Updated bio')
        self.assertEqual(self.frog.minecraft_username, 'UpdatedMine')
        self.assertEqual(self.frog.location, 'SwampNode-East-04')
        self.assertEqual(self.frog.tier, 'frog')
        self.assertTrue(self.frog.show_real_name)
        self.assertTrue(self.frog.show_active_modpacks)
        self.assertTrue(self.frog.show_last_played_server)
        self.assertTrue(self.frog.allow_friend_requests)
        self.assertTrue(self.frog.show_achievements)
        self.assertTrue(self.frog.allow_external_wall_posts)

    def test_profile_edit_view_updates_and_redirects(self):
        self.client.login(username='frogger', password='secret123')

        response = self.client.post(
            reverse('frogs-profile-edit'),
            {
                'username': 'frogger-updated',
                'first_name': 'New Name',
                'bio': 'Fresh terminal status',
                'minecraft_username': 'NewMine',
                'location': 'SwampNode-East-04',
                'show_real_name': 'public',
                'show_active_modpacks': 'on',
                'show_last_played_server': 'on',
                'allow_friend_requests': 'on',
                'show_achievements': 'on',
                'allow_external_wall_posts': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('frogs-profile-own'))
        self.user.refresh_from_db()
        self.frog.refresh_from_db()
        self.assertEqual(self.user.username, 'frogger-updated')
        self.assertEqual(self.user.first_name, 'New Name')
        self.assertEqual(self.frog.bio, 'Fresh terminal status')
        self.assertEqual(self.frog.minecraft_username, 'NewMine')
        self.assertEqual(self.frog.location, 'SwampNode-East-04')
        self.assertEqual(self.frog.tier, 'frog')


class WallPostTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='sender', password='secret123')
        self.target = User.objects.create_user(username='receiver', password='secret123')

    def test_wall_post_form_creates_post_from_text_only(self):
        form = WallPostForm(data={'text': 'Fresh log transmission'})

        self.assertTrue(form.is_valid(), form.errors)
        post = form.save(author=self.author, topic=self.target.wall)

        self.assertEqual(post.author, self.author)
        self.assertEqual(post.topic, self.target.wall)
        self.assertEqual(post.content, 'Fresh log transmission')
        self.assertEqual(post.title, 'Fresh log transmission')

    def test_wall_post_create_view_returns_rendered_post_payload(self):
        self.client.login(username='sender', password='secret123')

        response = self.client.post(
            reverse('frogs-wall-post-create', args=[self.target.id]),
            {'text': 'Transmit this to the wall'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('html', payload)
        self.assertIn('Transmit this to the wall', payload['html'])
        self.assertEqual(payload['count'], 1)

        post = ForumPost.objects.get(topic=self.target.wall)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.content, 'Transmit this to the wall')

    def test_wall_post_create_view_rejects_external_posts_when_disabled(self):
        self.target.frog.allow_external_wall_posts = False
        self.target.frog.save()
        self.client.login(username='sender', password='secret123')

        response = self.client.post(
            reverse('frogs-wall-post-create', args=[self.target.id]),
            {'text': 'Blocked transmission'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ForumPost.objects.filter(topic=self.target.wall).exists())
