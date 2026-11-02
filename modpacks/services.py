"""Business logic for the launcher modpack catalog and game-key redemption."""

import logging

from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import DatabaseError, transaction

from .models import GameKey, KeyRedemption, LauncherClient, Modpack, normalize_key_code

logger = logging.getLogger(__name__)


class RedemptionError(Exception):
    def __init__(self, code, message, status):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _image_url(field, request):
    if not field:
        return None
    url = field.url
    return request.build_absolute_uri(url) if request is not None else url


def unlocked_pack_ids(client):
    return set(Modpack.objects.unlocked_for(client).values_list("id", flat=True))


def serialize_build(pack, unlocked_ids):
    return {
        "slug": pack.slug,
        "name": pack.name,
        "version": pack.version,
        "is_release": pack.parent_id is None,
        "is_published": pack.is_published,
        "unlocked_by_key": pack.id in unlocked_ids,
        "git_url": pack.git_url,
        "git_branch": pack.git_branch,
        "minecraft_version": pack.minecraft_version,
        "mod_loader": pack.mod_loader,
        "loader_version": pack.loader_version,
        "updated_at": pack.updated_at.isoformat(),
    }


def serialize_entry(parent, visible_builds, unlocked_ids, request=None):
    return {
        "slug": parent.slug,
        "name": parent.name,
        "description": parent.description,
        "code": parent.code,
        "status": parent.status_label,
        "color": parent.color or None,
        "features": [line.strip() for line in parent.features.splitlines() if line.strip()],
        "icon": _image_url(parent.icon, request),
        "logo": _image_url(parent.logo, request),
        "background": _image_url(parent.background, request),
        "builds": [serialize_build(build, unlocked_ids) for build in visible_builds],
    }


def build_catalog(client, request=None, slug=None):
    """Return the list entries this launcher can see.

    A top-level pack is listed when it, or any of its builds, is published or
    unlocked for this client. Only the builds the client can access are
    included, so an unpublished release with an unlocked dev build lists the
    pack with just the dev build.
    """
    accessible_ids = set(Modpack.objects.accessible_to(client).values_list("id", flat=True))
    unlocked_ids = unlocked_pack_ids(client)

    parents = Modpack.objects.top_level().prefetch_related("builds")
    if slug is not None:
        parents = parents.filter(slug=slug)

    entries = []
    for parent in parents:
        candidates = [parent, *parent.builds.all()]
        visible = [pack for pack in candidates if pack.id in accessible_ids]
        if visible:
            entries.append(serialize_entry(parent, visible, unlocked_ids, request))
    return entries


def redeem_key(client, raw_code):
    """Redeem a key for a launcher. Returns ``(key, already_redeemed)``."""
    code = normalize_key_code(raw_code)
    if not code:
        raise RedemptionError("missing_code", "Enter a key.", 400)

    with transaction.atomic():
        key = (
            GameKey.objects.select_for_update(of=("self",))
            .select_related("modpack", "modpack__parent")
            .filter(code=code)
            .first()
        )
        if key is None or not key.is_active:
            raise RedemptionError("invalid_key", "That key is not valid.", 404)
        if KeyRedemption.objects.for_client(client).filter(key=key).exists():
            return key, True
        if key.is_expired:
            raise RedemptionError("expired_key", "That key has expired.", 410)
        if key.redemptions.count() >= key.max_uses:
            raise RedemptionError("key_used_up", "That key has already been used.", 409)
        KeyRedemption.objects.create(key=key, client=client, user_id=client.user_id)
    return key, False


class SignInError(Exception):
    def __init__(self, code, message, status):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# Failed sign-ins allowed per (IP, username) and per IP within the window.
SIGN_IN_WINDOW = 15 * 60
SIGN_IN_MAX_FAILURES = 10
SIGN_IN_MAX_FAILURES_PER_IP = 50


def _failure_keys(ip, username):
    return [
        (f"launcher-signin:{ip}:{username.lower()}", SIGN_IN_MAX_FAILURES),
        (f"launcher-signin:{ip}", SIGN_IN_MAX_FAILURES_PER_IP),
    ]


# The throttle fails open: if the cache is down (e.g. the database cache table
# is missing), sign-in still works, just without the attempt limit. The
# savepoint keeps a failed cache query from breaking the surrounding
# transaction on Postgres.

def _is_throttled(ip, username):
    try:
        with transaction.atomic():
            return any((cache.get(key) or 0) >= limit for key, limit in _failure_keys(ip, username))
    except DatabaseError:
        logger.warning("Launcher sign-in throttle unavailable (cache error)", exc_info=True)
        return False


def _record_failure(ip, username):
    try:
        with transaction.atomic():
            for key, _ in _failure_keys(ip, username):
                cache.add(key, 0, SIGN_IN_WINDOW)
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, SIGN_IN_WINDOW)
    except DatabaseError:
        logger.warning("Launcher sign-in throttle unavailable (cache error)", exc_info=True)


def sign_in(request, client, username, password, ip):
    """Check website credentials and sign the launcher in.

    Reuses the calling launcher's client when it has one, so keys it redeemed
    while signed out move into the account. Returns ``(client, token)``; the
    token is always new.
    """
    username = (username or "").strip()
    if not username or not password:
        raise SignInError("missing_credentials", "Enter your username and password.", 400)
    if _is_throttled(ip, username):
        raise SignInError("too_many_attempts", "Too many sign-in attempts. Try again in a few minutes.", 429)

    user = authenticate(request, username=username, password=password)
    if user is None:
        _record_failure(ip, username)
        raise SignInError("invalid_credentials", "Wrong username or password.", 401)

    with transaction.atomic():
        if client is None:
            client = LauncherClient(user=user)
        else:
            _claim_anonymous_redemptions(client, user)
            client.user = user
        token = client.rotate_token()
        client.save()
    return client, token


def _claim_anonymous_redemptions(client, user):
    anonymous = KeyRedemption.objects.filter(client=client, user__isnull=True)
    owned = KeyRedemption.objects.filter(user=user).values("key_id")
    # The account already has these keys; drop the duplicate.
    anonymous.filter(key_id__in=owned).delete()
    anonymous.update(user=user)


def sign_out(client):
    client.user = None
    client.save(update_fields=["user"])


def serialize_account(user, request=None):
    frog = getattr(user, "frog", None)
    return {
        "username": user.get_username(),
        "avatar": _image_url(frog.avatar, request) if frog else None,
        "minecraft_username": (frog.minecraft_username or None) if frog else None,
    }
