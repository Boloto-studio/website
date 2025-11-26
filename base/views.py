from django.utils import timezone
from .models import BlogPost, Event, HeroSlide
from django.shortcuts import render
from django.utils.translation import gettext as _

# Create your views here.


def home(request):
    # Fetch all upcoming events from the database
    events = Event.objects.all().order_by('date')
    # events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
    blog_counts = BlogPost.objects.count()
    blogs_posts = BlogPost.objects.all().order_by('-published_date')[:8]
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order', '-created_at')
    return render(request, "base/home.html", {
        "path_title": _("Home"),
        "events": events,
        "posts": blogs_posts,
        "extra_blogs": blog_counts > 8,
        "hero_slides": hero_slides,
    })
