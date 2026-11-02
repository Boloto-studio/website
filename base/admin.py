from django.contrib import admin

from .models import *

# Admin branding; the look itself lives in templates/admin/base_site.html
# and base/static/base/admin.css.
admin.site.site_header = "Admin terminal"
admin.site.site_title = "Boloto admin"
admin.site.index_title = "Control room"


admin.site.register(Event)
admin.site.register(BlogPost)
admin.site.register(Server)


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    # list_display = ['name', 'callsign', 'role', 'status', 'display_order']
    # list_editable = ['status', 'display_order']
    search_fields = ['name', 'callsign', 'role']


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    # list_display = ['title', 'order', 'is_active', 'created_at']
    # list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle']


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    # list_display = ['name', 'email', 'status', 'created_at']
    # list_filter = ['status', 'created_at']
    # list_editable = ['status']
    search_fields = ['name', 'email', 'message']


@admin.register(MainFocus)
class MainFocusAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Allow add only when no MainFocus instance exists
        if MainFocus.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Disallow delete from admin for safety; allow via code if needed
        return False
