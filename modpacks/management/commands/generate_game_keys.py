from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modpacks.models import GameKey, Modpack


class Command(BaseCommand):
    help = "Generate game keys that unlock a modpack (or one of its builds) and print them."

    def add_arguments(self, parser):
        parser.add_argument("slug", help="Slug of the pack or build the keys unlock.")
        parser.add_argument("--count", type=int, default=1)
        parser.add_argument("--max-uses", type=int, default=1, help="Launchers that can redeem each key.")
        parser.add_argument("--expires-in-days", type=int, help="Leave out for keys that never expire.")
        parser.add_argument("--note", default="")

    def handle(self, slug, count, max_uses, expires_in_days, note, **options):
        pack = Modpack.objects.filter(slug=slug).first()
        if pack is None:
            raise CommandError(f'No modpack with slug "{slug}".')
        if count < 1 or max_uses < 1:
            raise CommandError("--count and --max-uses must be at least 1.")

        expires_at = None
        if expires_in_days is not None:
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        keys = GameKey.objects.bulk_create(
            GameKey(modpack=pack, max_uses=max_uses, expires_at=expires_at, note=note)
            for _ in range(count)
        )
        self.stderr.write(f"Generated {len(keys)} key(s) for {pack}:")
        for key in keys:
            self.stdout.write(key.code)
