from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from .models import Frog, DonoSubscription


class DonoSubscriptionModelTests(TestCase):
    def test_only_one_subscription_per_frog(self):
        user = User.objects.create_user(username='frogger', password='secret123')
        frog = Frog.objects.get(user=user)

        DonoSubscription.objects.create(frog=frog, tier='frog')

        with self.assertRaises(IntegrityError):
            DonoSubscription.objects.create(frog=frog, tier='scavenger')
