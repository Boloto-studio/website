from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import FrogProfileEditForm, WallPostForm
from .models import Frog, ForumPost, FriendRequest


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


class FriendsListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='rosterlead', password='secret123', first_name='Lead')
        self.friend_online = User.objects.create_user(username='signal_one', password='secret123', first_name='Signal')
        self.friend_offline = User.objects.create_user(username='signal_two', password='secret123', first_name='Static')
        self.incoming = User.objects.create_user(username='incoming_node', password='secret123', first_name='Incoming')

        self.user.frog.location = 'Main Node'
        self.user.frog.save()

        self.friend_online.frog.location = 'Sector 7'
        self.friend_online.frog.minecraft_username = 'SignalCraft'
        self.friend_online.frog.save()

        self.friend_offline.frog.location = 'Outpost 19'
        self.friend_offline.frog.save()
        self.friend_offline.frog.last_active = self.friend_offline.frog.last_active.replace(year=2025)
        self.friend_offline.frog.save()

        self.user.frog.friends.add(self.friend_online, self.friend_offline)
        self.incoming_request = self.incoming.frog
        self.incoming_request.allow_friend_requests = True
        self.incoming_request.save()
        FriendRequest.objects.create(from_user=self.incoming_request, to_user=self.user)

    def test_friends_list_view_renders_roster_and_requests(self):
        self.client.login(username='rosterlead', password='secret123')

        response = self.client.get(reverse('frogs-friends'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/SYS/COMMS/FRIENDS')
        self.assertContains(response, 'PENDING INCOMING TRANSMISSIONS')
        self.assertContains(response, 'Signal')
        self.assertContains(response, 'Static')
        self.assertContains(response, 'Incoming')
        self.assertContains(response, reverse('frogs-profile', args=[self.friend_online.id]))
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'data-friend-request-action="accept"')

    def test_friends_list_view_shows_search_results_when_q_present(self):
        stranger = User.objects.create_user(username='swamp_scanner', password='secret123', first_name='Scanner')
        stranger.frog.location = 'Search Sector'
        stranger.frog.save()

        self.client.login(username='rosterlead', password='secret123')

        response = self.client.get(reverse('frogs-friends'), {'q': 'scanner'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swamp_scanner')
        self.assertNotContains(response, 'Static')
        self.assertContains(response, 'STATUS: MATCHES')

    def test_friend_request_delete_accepts_inbound_request(self):
        self.client.login(username='rosterlead', password='secret123')

        response = self.client.delete(reverse('frogs-friend-request', args=[self.incoming.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FriendRequest.objects.filter(from_user=self.incoming.frog, to_user=self.user).exists())

    def test_friend_request_put_accepts_inbound_request(self):
        self.client.login(username='rosterlead', password='secret123')

        response = self.client.put(reverse('frogs-friend-request', args=[self.incoming.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.frog.friends.filter(id=self.incoming.id).exists())
        self.assertFalse(FriendRequest.objects.filter(from_user=self.incoming.frog, to_user=self.user).exists())
