"""Business logic for the launcher modpack catalog and game-key redemption."""

from django.db import transaction

from .models import GameKey, KeyRedemption, Modpack, normalize_key_code


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
    if client is None:
        return set()
    return set(
        Modpack.objects.filter(game_keys__redemptions__client=client).values_list("id", flat=True)
    )


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
        if key.redemptions.filter(client=client).exists():
            return key, True
        if key.is_expired:
            raise RedemptionError("expired_key", "That key has expired.", 410)
        if key.redemptions.count() >= key.max_uses:
            raise RedemptionError("key_used_up", "That key has already been used.", 409)
        KeyRedemption.objects.create(key=key, client=client)
    return key, False
