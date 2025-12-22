from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Frog(models.Model):

    statuses = [
        ('online', 'Online'),
        ('ingame', 'In Game'),
        ('offline', 'Offline'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='frog')
    bio = models.TextField(blank=True)
    avatar = models.CharField(max_length=255, blank=True)
    following = models.ManyToManyField(User, blank=True, related_name='followers')
    status = models.CharField(max_length=255, choices=statuses, default='offline')
    last_active = models.DateTimeField(auto_now=True)
    minecraft_username = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username


# auto create / save profile for each user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Frog.objects.create(user=instance)
    instance.frog.save()