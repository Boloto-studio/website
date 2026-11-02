"""JSON API used by the Boloto launcher.

Launchers identify themselves with the token from ``POST /api/launcher/clients/``,
sent as ``Authorization: Bearer <token>``. The catalog works without a token
(published packs only); redeeming a key needs one.
"""

import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import LauncherClient
from .services import RedemptionError, build_catalog, redeem_key


def _error(code, message, status):
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def _client_from_request(request):
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    client = LauncherClient.from_token(token.strip())
    if client is not None:
        LauncherClient.objects.filter(pk=client.pk).update(last_seen_at=timezone.now())
    return client


@csrf_exempt
@require_POST
@never_cache
def register_client(request):
    client, token = LauncherClient.create_with_token()
    return JsonResponse({"token": token, "client_id": client.pk}, status=201)


@require_GET
@never_cache
def modpack_list(request):
    client = _client_from_request(request)
    return JsonResponse({"modpacks": build_catalog(client, request)})


@require_GET
@never_cache
def modpack_detail(request, slug):
    client = _client_from_request(request)
    entries = build_catalog(client, request, slug=slug)
    if not entries:
        return _error("not_found", "Modpack not found.", 404)
    return JsonResponse({"modpack": entries[0]})


@csrf_exempt
@require_POST
@never_cache
def redeem(request):
    client = _client_from_request(request)
    if client is None:
        return _error("unauthorized", "Register the launcher before redeeming keys.", 401)

    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("bad_request", "Body must be JSON.", 400)
    if not isinstance(body, dict):
        return _error("bad_request", "Body must be a JSON object.", 400)

    try:
        key, already_redeemed = redeem_key(client, str(body.get("code", "")))
    except RedemptionError as exc:
        return _error(exc.code, exc.message, exc.status)

    pack = key.modpack
    parent = pack.parent or pack
    entry = build_catalog(client, request, slug=parent.slug)[0]
    return JsonResponse({
        "already_redeemed": already_redeemed,
        "unlocked": {"slug": pack.slug, "name": str(pack)},
        "modpack": entry,
    })
