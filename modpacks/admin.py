import csv

from django.contrib import admin, messages
from django.db.models import Count
from django.http import HttpResponse

from .models import GameKey, KeyRedemption, LauncherClient, Modpack


class BuildInline(admin.TabularInline):
    model = Modpack
    fk_name = "parent"
    extra = 0
    fields = ["name", "slug", "version", "git_url", "git_branch", "is_published", "order"]
    show_change_link = True
    verbose_name = "build"
    verbose_name_plural = "builds"


class GameKeyInline(admin.TabularInline):
    model = GameKey
    extra = 0
    fields = ["code", "max_uses", "expires_at", "is_active", "note"]
    readonly_fields = ["code"]
    show_change_link = True


def generate_keys_action(count):
    def action(modeladmin, request, queryset):
        for pack in queryset:
            GameKey.objects.bulk_create(GameKey(modpack=pack) for _ in range(count))
        messages.success(
            request,
            f"Generated {count} key(s) for {queryset.count()} pack(s). "
            "Find them under Game keys.",
        )

    action.__name__ = f"generate_{count}_keys"
    action.short_description = f"Generate {count} single-use key(s)"
    return action


@admin.register(Modpack)
class ModpackAdmin(admin.ModelAdmin):
    list_display = ["__str__", "slug", "git_branch", "is_published", "order", "updated_at"]
    list_editable = ["is_published", "order"]
    list_filter = ["is_published", "parent"]
    search_fields = ["name", "slug", "git_url"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["parent"]
    inlines = [BuildInline, GameKeyInline]
    actions = [generate_keys_action(1), generate_keys_action(10)]
    fieldsets = [
        (None, {"fields": ["parent", "name", "slug", "description", "version", "is_published", "order"]}),
        ("Source", {"fields": ["git_url", "git_branch"]}),
        ("Game", {"fields": ["minecraft_version", "mod_loader", "loader_version"]}),
        ("Launcher presentation", {
            "description": "Used on top-level packs only.",
            "fields": ["code", "status_label", "color", "features", "icon", "logo", "background"],
        }),
    ]

    def get_readonly_fields(self, request, obj=None):
        # A pack with builds must stay top-level, so don't offer a parent.
        if obj is not None and obj.builds.exists():
            return ["parent"]
        return []

    def get_inlines(self, request, obj):
        # Builds can't have builds of their own.
        if obj is not None and obj.parent_id:
            return [GameKeyInline]
        return super().get_inlines(request, obj)


@admin.register(GameKey)
class GameKeyAdmin(admin.ModelAdmin):
    list_display = ["code", "modpack", "uses", "max_uses", "expires_at", "is_active", "note", "created_at"]
    list_filter = ["is_active", "modpack"]
    search_fields = ["code", "note", "modpack__name"]
    autocomplete_fields = ["modpack"]
    actions = ["export_csv", "deactivate"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("modpack", "modpack__parent").annotate(
            _uses=Count("redemptions")
        )

    @admin.display(description="Uses", ordering="_uses")
    def uses(self, obj):
        return obj._uses

    def get_readonly_fields(self, request, obj=None):
        # Keep the code fixed once the key exists; it may already be handed out.
        return ["code"] if obj else []

    @admin.action(description="Export selected keys as CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="game_keys.csv"'
        writer = csv.writer(response)
        writer.writerow(["code", "modpack", "max_uses", "uses", "expires_at", "note"])
        for key in queryset:
            writer.writerow([key.code, str(key.modpack), key.max_uses, key._uses, key.expires_at or "", key.note])
        return response

    @admin.action(description="Deactivate selected keys")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f"Deactivated {updated} key(s).")


@admin.register(KeyRedemption)
class KeyRedemptionAdmin(admin.ModelAdmin):
    list_display = ["key", "user", "client", "redeemed_at"]
    list_select_related = ["key__modpack", "client", "user"]
    search_fields = ["key__code", "user__username", "client__minecraft_username"]
    raw_id_fields = ["key", "client", "user"]


@admin.register(LauncherClient)
class LauncherClientAdmin(admin.ModelAdmin):
    list_display = ["__str__", "user", "minecraft_username", "created_at", "last_seen_at"]
    list_select_related = ["user"]
    search_fields = ["user__username", "minecraft_username", "minecraft_uuid"]
    raw_id_fields = ["user"]
    readonly_fields = ["created_at", "last_seen_at"]
