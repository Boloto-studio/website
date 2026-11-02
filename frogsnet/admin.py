from django.contrib import admin

from frogsnet.models import FriendRequest, Frog, ForumPost, ForumTopic, ModpackStat

admin.site.register(ModpackStat) 

class FriendRequestInline(admin.TabularInline):
    model = FriendRequest
    fk_name = "from_user"
    extra = 0
    fields = ("from_user", "to_user", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
class ForumPostReplyInline(admin.TabularInline):
    model = ForumPost
    fk_name = "response_to"
    extra = 0
    fields = ("title", "author", "topic", "content", "published_date")
    readonly_fields = ("published_date",)
    ordering = ("-published_date",)


class ForumTopicPostInline(admin.TabularInline):
    model = ForumPost
    fk_name = "topic"
    extra = 0
    fields = ("title", "author", "response_to", "content", "published_date")
    readonly_fields = ("published_date",)
    ordering = ("-published_date",)


@admin.register(Frog)
class FrogAdmin(admin.ModelAdmin):
    inlines = [FriendRequestInline]
    search_fields = ["user__username", "minecraft_username"]


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    inlines = [ForumPostReplyInline]
    list_display = ("title", "author", "topic", "published_date")
    list_filter = ("topic", "author")
    search_fields = ("title", "content", "author__username")


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    inlines = [ForumTopicPostInline]
    list_display = ("title", "owner_if_wall", "created_at")
    list_filter = ("owner_if_wall", "created_at")
    search_fields = ("title", "description", "owner_if_wall__username")