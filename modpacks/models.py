import hashlib
import secrets

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

# Unambiguous alphabet for game keys: no 0/O, 1/I/L, so codes are easy to type.
KEY_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
KEY_GROUPS = 4
KEY_GROUP_LENGTH = 5


def generate_key_code():
    """Return a random key such as ``7KQ2M-XW4PA-93HTN-RC8VE``."""
    groups = [
        "".join(secrets.choice(KEY_ALPHABET) for _ in range(KEY_GROUP_LENGTH))
        for _ in range(KEY_GROUPS)
    ]
    return "-".join(groups)


def normalize_key_code(raw):
    """Uppercase a user-typed key and re-insert dashes, so ``7kq2m xw4pa…``
    and ``7KQ2MXW4PA…`` both match the stored ``7KQ2M-XW4PA-…``."""
    chars = "".join(c for c in (raw or "").upper() if c.isalnum())
    return "-".join(
        chars[i:i + KEY_GROUP_LENGTH] for i in range(0, len(chars), KEY_GROUP_LENGTH)
    )


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ModpackQuerySet(models.QuerySet):
    def top_level(self):
        return self.filter(parent__isnull=True)

    def accessible_to(self, client):
        """Packs that are published, or unlocked by a key the client redeemed."""
        query = models.Q(is_published=True)
        if client is not None:
            query |= models.Q(game_keys__redemptions__client=client)
        return self.filter(query).distinct()


class Modpack(models.Model):
    """A modpack shown in the Boloto launcher.

    A pack with no parent is a list entry, and is itself the release build.
    Packs whose ``parent`` is set are extra builds of that entry (dev, beta…).
    """

    LOADER_CHOICES = [
        ("forge", "Forge"),
        ("neoforge", "NeoForge"),
        ("fabric", "Fabric"),
        ("quilt", "Quilt"),
    ]

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="builds",
        limit_choices_to={"parent__isnull": True},
        help_text="Leave empty for a top-level pack. Set it to make this a build "
                  "(dev, beta…) of another pack.",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, blank=True)

    git_url = models.URLField(max_length=500, help_text="Repository the launcher pulls the pack from.")
    git_branch = models.CharField(max_length=200, default="main")

    minecraft_version = models.CharField(max_length=20, blank=True)
    mod_loader = models.CharField(max_length=20, choices=LOADER_CHOICES, blank=True)
    loader_version = models.CharField(max_length=50, blank=True)

    # How the pack is drawn in the launcher. Only used on top-level packs.
    code = models.CharField(max_length=12, blank=True, help_text='Short tape label, e.g. "VTR-02".')
    status_label = models.CharField(max_length=40, blank=True, help_text='e.g. "IN DEVELOPMENT".')
    color = models.CharField(
        max_length=7,
        blank=True,
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use a hex color like #FFB000.")],
        help_text="Tape label color, e.g. #FFB000.",
    )
    features = models.TextField(blank=True, help_text="Track list shown in the launcher, one feature per line.")

    icon = models.ImageField(
        upload_to="modpacks/icons/", blank=True, null=True,
        help_text="Square logo on a transparent background; the launcher tints it.",
    )
    logo = models.ImageField(upload_to="modpacks/logos/", blank=True, null=True)
    background = models.ImageField(upload_to="modpacks/backgrounds/", blank=True, null=True)

    is_published = models.BooleanField(
        default=False,
        help_text="Published packs show up for everyone. Unpublished ones only "
                  "show up for launchers that redeemed a key for them.",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ModpackQuerySet.as_manager()

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        if self.parent_id:
            return f"{self.parent.name} / {self.name}"
        return self.name

    def clean(self):
        if self.parent_id is None:
            return
        if self.parent_id == self.pk:
            raise ValidationError({"parent": "A pack cannot be its own parent."})
        if self.parent.parent_id is not None:
            raise ValidationError({"parent": "Builds cannot have builds of their own; pick a top-level pack."})
        if self.pk and self.builds.exists():
            raise ValidationError({"parent": "This pack has builds, so it must stay top-level."})


class LauncherClient(models.Model):
    """One launcher install. It authenticates with a random token the server
    issued; only the token's hash is stored. Once Microsoft sign-in exists,
    the Minecraft account can be attached here."""

    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    minecraft_uuid = models.CharField(max_length=36, blank=True)
    minecraft_username = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.minecraft_username or f"Launcher #{self.pk}"

    @classmethod
    def create_with_token(cls):
        token = secrets.token_urlsafe(32)
        client = cls.objects.create(token_hash=hash_token(token))
        return client, token

    @classmethod
    def from_token(cls, token):
        if not token:
            return None
        return cls.objects.filter(token_hash=hash_token(token)).first()


class GameKey(models.Model):
    """A key that unlocks one pack (a top-level pack or one of its builds)."""

    code = models.CharField(max_length=32, unique=True, default=generate_key_code)
    modpack = models.ForeignKey(Modpack, on_delete=models.CASCADE, related_name="game_keys")
    max_uses = models.PositiveIntegerField(default=1, help_text="How many launchers can redeem this key.")
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True, help_text="Who the key was given to, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} → {self.modpack}"

    def save(self, *args, **kwargs):
        self.code = normalize_key_code(self.code)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()


class KeyRedemption(models.Model):
    key = models.ForeignKey(GameKey, on_delete=models.CASCADE, related_name="redemptions")
    client = models.ForeignKey(LauncherClient, on_delete=models.CASCADE, related_name="redemptions")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-redeemed_at"]
        constraints = [
            models.UniqueConstraint(fields=["key", "client"], name="unique_key_per_client"),
        ]

    def __str__(self):
        return f"{self.key.code} by {self.client}"
