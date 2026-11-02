from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import markdown2
import nh3
from django.utils.text import slugify
from bs4 import BeautifulSoup
import ipinfo
from django.conf import settings
import requests

# Create your models here.

EVENT_TYPES = [
    ("stream", "Live stream"),
    ("trailer", "Trailer drop"),
]

class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.URLField(help_text="URL of the background image")
    link = models.URLField(blank=True, null=True)
    link_text = models.CharField(
        max_length=100, blank=True, default="Learn More")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vertical_align = models.CharField(max_length=20, choices=[
        ("top", "Top"),
        ("center", "Center"),
        ("bottom", "Bottom"),
    ], default="center")
    horizontal_align = models.CharField(max_length=20, choices=[
        ("left", "Left"),
        ("center", "Center"),
        ("right", "Right"),
    ], default="center")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-created_at']


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=100, choices=EVENT_TYPES)
    link = models.URLField(blank=True, null=True)

    # YouTube integration fields
    youtube_video_id = models.CharField(
        max_length=50, blank=True, null=True, unique=True)
    scheduled_start_time = models.DateTimeField(blank=True, null=True)

    # Sync tracking
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']

    def is_upcoming(self):
        return self.date >= timezone.now()

class AbstractPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def parse_html_content(self):
        """
        Parses the content of the blog post and returns it as HTML.
        """
        unsafe_html = markdown2.markdown(self.content)
        safe_html = nh3.clean(unsafe_html)
        return safe_html

    @property
    def clean_preview(self):
        """
        Returns a cleaned preview of the content.
        """
        preview_length = 250

        unsafe_html = markdown2.markdown(self.content[:preview_length])
        safe_html = nh3.clean(unsafe_html)
        soup = BeautifulSoup(safe_html, "html.parser")

        for img in soup.find_all("img"):
            img.decompose()

        plain_text = soup.get_text(separator=" ").strip()
        return plain_text

    def __str__(self):
        return self.title

class BlogPost(AbstractPost):
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="blog_posts")

class StaffMember(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='staff_profile')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField(blank=True, max_length=200)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    discord_url = models.URLField(blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class ContactRequest(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField(max_length=2000)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"


class MainFocus(models.Model):
    text = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and MainFocus.objects.exists():
            raise ValidationError("Only one MainFocus instance is allowed.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return (self.text[:50] + '...') if self.text and len(self.text) > 50 else (self.text or 'Main Focus')

class Modpack(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def icon_asset_name(self):
        return f"{slugify(self.name).replace('-', '_')}_icon.png"

    def __str__(self):
        return self.name

class Server(models.Model):
    regions = [
        ("NA", "North America"),
        ("EU", "Europe"),
        ("AS", "Asia"),
        ("SA", "South America"),
        ("AF", "Africa"),
        ("OC", "Oceania"),
    ]

    name = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField()
    localhost_ip = models.GenericIPAddressField(blank=True, null=True, help_text="Optional local IP address for internal use")
    is_featured = models.BooleanField(default=False)
    server_id = models.CharField(max_length=100, blank=True, null=True, help_text="Crafty's server ID for fetching server details")
    port = models.PositiveIntegerField(default=25565)
    description = models.TextField(blank=True)
    world_size = models.CharField(blank=True, null=True, max_length=50, help_text="Size of the world in MB")
    modpack = models.ForeignKey(Modpack, on_delete=models.CASCADE, related_name="servers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    region = models.CharField(max_length=2, choices=regions, blank=True, null=True)
    is_online = models.BooleanField(default=False, help_text="Indicates if the server is currently online")
    current_players = models.PositiveIntegerField(default=0, help_text="Current number of players on the server")
    max_players = models.PositiveIntegerField(default=10, help_text="Maximum number of players allowed on the server")

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"

    def determine_region(self):
        """
        Determines the region of the server based on its IP address.
        """
        handler = ipinfo.getHandler(settings.IPINFO_TOKEN)
        details = handler.getDetails(self.ip_address)
        return details.continent

    def update_details(self):
        """
        Updates the server's details.
        """
        API_ADDRESS = f"http://{self.localhost_ip}" if self.localhost_ip else f"http://{self.ip_address}"
        if not self.server_id:
            try:
                response = requests.get(f"{API_ADDRESS}/api/v2/servers")
                response.raise_for_status()
                self.server_id = response.json()["data"][0].get("server_id")
            except requests.RequestException as e:
                print(f"Error fetching server ID: {e}")
        server_id = self.server_id
        stats_response = requests.get(f"{API_ADDRESS}/api/v2/servers/{server_id}/stats")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            self.name = stats_data["data"].get("server_name", self.name)
            self.world_size = stats_data.get("world_size", self.world_size)
            self.port = stats_data.get("server_port", self.port)
            self.description = stats_data.get("desc", self.description)
            self.updated_at = timezone.now()
            self.is_online = stats_data.get("running", self.is_online)
            self.current_players = stats_data.get("online", self.current_players)
            self.max_players = stats_data.get("max", self.max_players)
        else:
            print(f"Failed to fetch server stats for {self.name}. Status code: {stats_response.status_code}")
            self.is_online = False
        self.save()

    @classmethod
    def startup_server(cls, ip_address, localhost_ip=None):
        """
        Initializes a server instance at startup.
        """
        server, _ = cls.objects.get_or_create(ip_address=ip_address, defaults={'localhost_ip': localhost_ip})
        server.update_details()
        return server