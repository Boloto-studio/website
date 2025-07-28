from django.contrib.auth.models import User
from django.db import models

class ServerInstance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    crafty_server_id = models.IntegerField(null=True, blank=True)
    crafty_uuid = models.CharField(max_length=128, null=True, blank=True)
    ram_min = models.SmallIntegerField()  # in GB
    ram_max = models.SmallIntegerField()  # in GB
    created = models.DateTimeField(auto_now_add=True)
