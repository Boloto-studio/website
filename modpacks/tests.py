import json
from datetime import timedelta
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import GameKey, LauncherClient, Modpack, normalize_key_code


def make_pack(slug, parent=None, published=False, **extra):
    return Modpack.objects.create(
        slug=slug, name=slug.title(), parent=parent, is_published=published,
        git_url=f"https://github.com/boloto-studio/{slug}", **extra,
    )


class ApiTestCase(TestCase):
    def register(self):
        response = self.client.post(reverse("modpacks:register_client"))
        self.assertEqual(response.status_code, 201)
        return response.json()["token"]

    def auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def catalog(self, token=None):
        extra = self.auth(token) if token else {}
        response = self.client.get(reverse("modpacks:modpack_list"), **extra)
        self.assertEqual(response.status_code, 200)
        return response.json()["modpacks"]

    def redeem(self, token, code):
        return self.client.post(
            reverse("modpacks:redeem_key"), data=json.dumps({"code": code}),
            content_type="application/json", **self.auth(token),
        )


class CatalogTests(ApiTestCase):
    def setUp(self):
        self.vatra = make_pack(
            "vatra", published=True, git_branch="release", code="VTR-02", color="#FFB000",
            features="Village building\n\n Magic & dragons ",
        )
        self.vatra_dev = make_pack("vatra-dev", parent=self.vatra, git_branch="dev")
        self.vatra_beta = make_pack("vatra-beta", parent=self.vatra, published=True, git_branch="beta")
        self.secret = make_pack("secret")
        self.secret_dev = make_pack("secret-dev", parent=self.secret)

    def test_anonymous_sees_only_published(self):
        catalog = self.catalog()
        self.assertEqual([e["slug"] for e in catalog], ["vatra"])
        self.assertEqual(catalog[0]["code"], "VTR-02")
        self.assertEqual(catalog[0]["color"], "#FFB000")
        self.assertEqual(catalog[0]["features"], ["Village building", "Magic & dragons"])
        builds = catalog[0]["builds"]
        self.assertEqual([b["slug"] for b in builds], ["vatra", "vatra-beta"])
        self.assertTrue(builds[0]["is_release"])
        self.assertEqual(builds[0]["git_branch"], "release")
        self.assertEqual(builds[0]["git_url"], "https://github.com/boloto-studio/vatra")

    def test_builds_are_not_listed_as_top_level_entries(self):
        slugs = [e["slug"] for e in self.catalog()]
        self.assertNotIn("vatra-beta", slugs)

    def test_unknown_token_is_treated_as_anonymous(self):
        self.assertEqual([e["slug"] for e in self.catalog("not-a-token")], ["vatra"])

    def test_detail(self):
        response = self.client.get(reverse("modpacks:modpack_detail", args=["vatra"]))
        self.assertEqual(response.json()["modpack"]["slug"], "vatra")
        hidden = self.client.get(reverse("modpacks:modpack_detail", args=["secret"]))
        self.assertEqual(hidden.status_code, 404)
        build = self.client.get(reverse("modpacks:modpack_detail", args=["vatra-beta"]))
        self.assertEqual(build.status_code, 404)

    def test_published_build_of_unpublished_pack_lists_the_parent(self):
        make_pack("open-beta", parent=self.secret, published=True)
        entry = next(e for e in self.catalog() if e["slug"] == "secret")
        self.assertEqual([b["slug"] for b in entry["builds"]], ["open-beta"])


class RedemptionTests(ApiTestCase):
    def setUp(self):
        self.vatra = make_pack("vatra")  # release not published yet
        self.vatra_dev = make_pack("vatra-dev", parent=self.vatra, git_branch="dev")
        self.token = self.register()

    def test_dev_key_unlocks_dev_build_of_unpublished_pack(self):
        key = GameKey.objects.create(modpack=self.vatra_dev)
        self.assertEqual(self.catalog(self.token), [])

        response = self.redeem(self.token, key.code)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["already_redeemed"])
        self.assertEqual(body["unlocked"]["slug"], "vatra-dev")
        self.assertEqual([b["slug"] for b in body["modpack"]["builds"]], ["vatra-dev"])

        catalog = self.catalog(self.token)
        self.assertEqual([e["slug"] for e in catalog], ["vatra"])
        dev = catalog[0]["builds"][0]
        self.assertEqual(dev["slug"], "vatra-dev")
        self.assertTrue(dev["unlocked_by_key"])
        self.assertEqual(dev["git_branch"], "dev")

        # Other launchers still see nothing.
        self.assertEqual(self.catalog(self.register()), [])
        self.assertEqual(self.catalog(), [])

    def test_parent_key_unlocks_release_only(self):
        key = GameKey.objects.create(modpack=self.vatra)
        self.redeem(self.token, key.code)
        builds = self.catalog(self.token)[0]["builds"]
        self.assertEqual([b["slug"] for b in builds], ["vatra"])

    def test_code_is_case_and_dash_insensitive(self):
        key = GameKey.objects.create(modpack=self.vatra)
        typed = key.code.replace("-", " ").lower()
        self.assertEqual(self.redeem(self.token, typed).status_code, 200)

    def test_redeeming_twice_is_idempotent(self):
        key = GameKey.objects.create(modpack=self.vatra)
        self.redeem(self.token, key.code)
        again = self.redeem(self.token, key.code)
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.json()["already_redeemed"])
        self.assertEqual(key.redemptions.count(), 1)

    def test_single_use_key_cannot_be_shared(self):
        key = GameKey.objects.create(modpack=self.vatra)
        self.redeem(self.token, key.code)
        response = self.redeem(self.register(), key.code)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "key_used_up")

    def test_multi_use_key(self):
        key = GameKey.objects.create(modpack=self.vatra, max_uses=2)
        self.assertEqual(self.redeem(self.register(), key.code).status_code, 200)
        self.assertEqual(self.redeem(self.register(), key.code).status_code, 200)
        self.assertEqual(self.redeem(self.register(), key.code).status_code, 409)

    def test_invalid_inactive_and_expired_keys(self):
        self.assertEqual(self.redeem(self.token, "AAAAA-BBBBB").status_code, 404)
        inactive = GameKey.objects.create(modpack=self.vatra, is_active=False)
        self.assertEqual(self.redeem(self.token, inactive.code).status_code, 404)
        expired = GameKey.objects.create(modpack=self.vatra, expires_at=timezone.now() - timedelta(days=1))
        self.assertEqual(self.redeem(self.token, expired.code).status_code, 410)
        self.assertEqual(self.redeem(self.token, "").status_code, 400)

    def test_redeem_requires_registered_launcher(self):
        key = GameKey.objects.create(modpack=self.vatra)
        response = self.client.post(
            reverse("modpacks:redeem_key"), data=json.dumps({"code": key.code}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.redeem("bogus", key.code).status_code, 401)

    def test_bad_json(self):
        response = self.client.post(
            reverse("modpacks:redeem_key"), data="nope", content_type="application/json",
            **self.auth(self.token),
        )
        self.assertEqual(response.status_code, 400)


class ModelTests(TestCase):
    def test_token_is_stored_hashed(self):
        client, token = LauncherClient.create_with_token()
        self.assertNotEqual(client.token_hash, token)
        self.assertEqual(LauncherClient.from_token(token), client)

    def test_builds_cannot_be_nested(self):
        root = make_pack("root")
        build = make_pack("build", parent=root)
        nested = Modpack(slug="nested", name="Nested", parent=build, git_url="https://example.com/x")
        with self.assertRaises(ValidationError):
            nested.full_clean()
        root.parent = make_pack("other")
        with self.assertRaises(ValidationError):
            root.full_clean()

    def test_normalize_key_code(self):
        self.assertEqual(normalize_key_code(" abcde fghjk-mnpqr "), "ABCDE-FGHJK-MNPQR")

    def test_generate_command(self):
        make_pack("vatra")
        out = StringIO()
        call_command("generate_game_keys", "vatra", "--count", "3", stdout=out, stderr=StringIO())
        codes = out.getvalue().split()
        self.assertEqual(len(codes), 3)
        self.assertEqual(GameKey.objects.filter(code__in=codes).count(), 3)


class SignInTests(ApiTestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from django.core.cache import cache

        cache.clear()
        self.user = User.objects.create_user("mavka", password="lisova-pisnya")
        self.vatra = make_pack("vatra")
        self.vatra_dev = make_pack("vatra-dev", parent=self.vatra)

    def login(self, username="mavka", password="lisova-pisnya", token=None):
        extra = self.auth(token) if token else {}
        return self.client.post(
            reverse("modpacks:login"), data=json.dumps({"username": username, "password": password}),
            content_type="application/json", **extra,
        )

    def me(self, token):
        return self.client.get(reverse("modpacks:me"), **self.auth(token))

    def test_login_returns_token_and_account(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["account"]["username"], "mavka")
        self.assertEqual(self.me(body["token"]).json()["account"]["username"], "mavka")

    def test_wrong_password(self):
        response = self.login(password="nope")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "invalid_credentials")
        self.assertEqual(self.login(username="", password="").status_code, 400)

    def test_inactive_user_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 401)

    def test_repeated_failures_are_throttled(self):
        from .services import SIGN_IN_MAX_FAILURES

        for _ in range(SIGN_IN_MAX_FAILURES):
            self.assertEqual(self.login(password="nope").status_code, 401)
        response = self.login()  # even the right password
        self.assertEqual(response.status_code, 429)

    def test_sign_in_rotates_token_and_claims_anonymous_keys(self):
        token = self.register()
        key = GameKey.objects.create(modpack=self.vatra_dev)
        self.redeem(token, key.code)

        new_token = self.login(token=token).json()["token"]
        self.assertNotEqual(new_token, token)
        self.assertEqual(self.catalog(token), [])  # old token is gone → anonymous
        self.assertEqual(LauncherClient.objects.count(), 1)
        self.assertEqual(key.redemptions.get().user, self.user)

        # The unlock now follows the account to another PC.
        elsewhere = self.login().json()["token"]
        builds = self.catalog(elsewhere)[0]["builds"]
        self.assertEqual([b["slug"] for b in builds], ["vatra-dev"])

    def test_keys_redeemed_while_signed_in_belong_to_the_account(self):
        token = self.login().json()["token"]
        key = GameKey.objects.create(modpack=self.vatra, max_uses=5)
        self.redeem(token, key.code)

        # Same account on a second PC: already redeemed, no extra use spent.
        second = self.login().json()["token"]
        again = self.redeem(second, key.code)
        self.assertTrue(again.json()["already_redeemed"])
        self.assertEqual(key.redemptions.count(), 1)

    def test_sign_out_hides_account_unlocks(self):
        token = self.login().json()["token"]
        key = GameKey.objects.create(modpack=self.vatra)
        self.redeem(token, key.code)
        self.assertEqual(len(self.catalog(token)), 1)

        response = self.client.post(reverse("modpacks:logout"), **self.auth(token))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.me(token).json()["account"])
        self.assertEqual(self.catalog(token), [])

    def test_claiming_a_key_the_account_already_has(self):
        key = GameKey.objects.create(modpack=self.vatra, max_uses=2)
        self.redeem(self.login().json()["token"], key.code)
        anon = self.register()
        self.redeem(anon, key.code)
        self.login(token=anon)
        self.assertEqual(key.redemptions.count(), 1)

    def test_deactivated_user_is_signed_out(self):
        token = self.login().json()["token"]
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(self.me(token).json()["account"])

    def test_me_and_logout_need_a_known_token(self):
        self.assertEqual(self.me("bogus").status_code, 401)
        self.assertEqual(self.client.post(reverse("modpacks:logout")).status_code, 401)
