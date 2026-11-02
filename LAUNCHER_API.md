# Launcher API

The `modpacks` app is the source of truth for the modpack list in the Boloto launcher.
Everything is managed by hand in the Django admin under **Modpacks**.

## How packs are organised

- **Modpack with no parent**: one entry in the launcher's list. It is also that pack's
  *release* build (it has its own `git_url` / `git_branch`).
- **Modpack with a parent**: an extra build of that entry (dev, beta…). Builds can't
  have builds of their own.
- **`is_published`**: published packs and builds show up for everyone. Unpublished ones
  only show up for launchers that redeemed a key for them.

An entry is listed when the parent **or any of its builds** is visible to that launcher,
and only the visible builds are returned. So a launcher that redeemed a key for
`vatra-dev` while `vatra` (the release) is still unpublished gets the Vatra entry with
just the dev build in it.

## Game keys

A key unlocks exactly one pack: the top-level pack (the release build) or one specific
build. Keys look like `7KQ2M-XW4PA-93HTN-RC8VE`; redemption ignores case, spaces and dashes.

Create keys in any of these ways:

- Admin → Modpacks → select packs → *Generate 1 / 10 single-use key(s)*
- Admin → Game keys → *Add* (the code is filled in for you; set uses, expiry, note)
- `python manage.py generate_game_keys vatra-dev --count 20 --max-uses 1 --expires-in-days 30 --note "Playtest"`

Admin → Game keys has *Export selected keys as CSV* and *Deactivate selected keys*.

## Endpoints

All responses are JSON. Base path: `/api/launcher/` (not language-prefixed).

Until Microsoft sign-in exists, a launcher install is identified by a token the server
issues. Send it as `Authorization: Bearer <token>`. Only its SHA-256 hash is stored.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `clients/` | none | Register a launcher install → `{"token": "...", "client_id": 1}` |
| GET | `modpacks/` | optional | Modpacks visible to this launcher |
| GET | `modpacks/<slug>/` | optional | One top-level entry (404 if not visible) |
| POST | `keys/redeem/` | required | Body `{"code": "..."}` |

`GET modpacks/` response:

```json
{
  "modpacks": [
    {
      "slug": "vatra",
      "name": "Vatra",
      "description": "...",
      "code": "VTR-02",
      "status": "IN DEVELOPMENT",
      "color": "#FFB000",
      "features": ["Village building & hired squads", "Magic & dragons"],
      "icon": "https://boloto.studio/media/modpacks/icons/vatra.png",
      "logo": null,
      "background": null,
      "builds": [
        {
          "slug": "vatra-dev",
          "name": "Dev",
          "version": "0.4.0",
          "is_release": false,
          "is_published": false,
          "unlocked_by_key": true,
          "git_url": "https://github.com/boloto-studio/vatra",
          "git_branch": "dev",
          "minecraft_version": "1.20.1",
          "mod_loader": "forge",
          "loader_version": "47.3.0",
          "updated_at": "2026-11-02T21:05:07.683122+00:00"
        }
      ]
    }
  ]
}
```

`POST keys/redeem/` returns `{"already_redeemed": false, "unlocked": {"slug", "name"}, "modpack": <entry>}`.
Redeeming a key you already redeemed is not an error (`already_redeemed: true`).

Errors look like `{"error": {"code": "...", "message": "..."}}`:

| Status | `code` | When |
| --- | --- | --- |
| 400 | `missing_code` / `bad_request` | Empty code or body that isn't a JSON object |
| 401 | `unauthorized` | No token, or an unknown token |
| 404 | `invalid_key` | No such key, or it was deactivated |
| 409 | `key_used_up` | All `max_uses` already redeemed by other launchers |
| 410 | `expired_key` | Past `expires_at` |

## Tests

```bash
python manage.py test modpacks
```

The `base` app has a Postgres-only migration (`0011`), so the test run needs Postgres
(set `DB_STRING`); on SQLite it fails while migrating `base`, before reaching these tests.
