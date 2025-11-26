from django.contrib import admin
from .models import BlogPost, Event, HeroSlide

# Register your models here.

admin.site.register(Event)
admin.site.register(BlogPost)


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle']
