from django.contrib import messages
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils import timezone

from .forms import ContactRequestForm
from .models import BlogPost, Event, HeroSlide, MainFocus, StaffMember

# Create your views here.


def _build_terminal_logs():
    video_logs = []
    synced_videos = Event.objects.exclude(youtube_video_id__isnull=True).exclude(
        youtube_video_id=""
    ).order_by('-date')[:3]

    for video in synced_videos:
        playback_url = video.link or f"https://www.youtube.com/watch?v={video.youtube_video_id}"
        video_logs.append({
            "title": video.title,
            "summary": video.description,
            "timestamp": video.date,
            "kind": _("MEDIA_FILE"),
            "action_label": _("Play transmission"),
            "url": playback_url,
            "thumbnail": f"https://img.youtube.com/vi/{video.youtube_video_id}/hqdefault.jpg",
        })

    text_logs = [{
        "title": post.title,
        "summary": post.content,
        "timestamp": post.published_date,
        "kind": _("TEXT_LOG"),
        "action_label": _("Read full log"),
        "url": "",
        "thumbnail": "",
    } for post in BlogPost.objects.all().order_by('-published_date')[:6]]

    combined_logs = sorted(
        [*video_logs, *text_logs],
        key=lambda item: item["timestamp"],
        reverse=True,
    )
    return combined_logs[:6]

def _donation_tiers():
    return [
        {
            "slug": "scavenger",
            "name": _("Scavenger"),
            "price": "$5",
            "interval": _("month"),
            "features": [_("Discord role"), _("Early updates")],
            "button_label": "select-scavenger.sh",
            "link": "",
            "featured": False,
        },
        {
            "slug": "operative",
            "name": _("Operative"),
            "price": "$15",
            "interval": _("month"),
            "features": [_("Discord role"), _("Early updates"), _("Beta server access")],
            "button_label": "select-operative.sh",
            "link": "",
            "featured": True,
        },
        {
            "slug": "overseer",
            "name": _("Overseer"),
            "price": "$30",
            "interval": _("month"),
            "features": [_("Discord role"), _("Beta server access"), _("Hall of fame")],
            "button_label": "select-overseer.sh",
            "link": "",
            "featured": False,
        },
    ]


def home(request):
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order', '-created_at')
    return render(request, "base/home.html", {
        "hero_slides": hero_slides,
        "terminal_logs": _build_terminal_logs(),
    })


def studio(request):
    return render(request, "base/studio.html", {
        "staff": StaffMember.objects.all(),
        "main_focus": MainFocus.objects.first(),
    })

def donation(request):
    return render(request, "base/donation.html", {
        "funding_progress": 80,
        "donation_tiers": _donation_tiers(),
    })

def under_construction(request):
    return render(request, "base/under_construction.html")

def contact(request):
    if request.method == "POST":
        form = ContactRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Transmission received. We will respond when the line is clear."))
            return render(request, "base/contact.html", {
                "nav_key": "contact",
                "form": ContactRequestForm(),
                "transmission_complete": True,
            })
    else:
        form = ContactRequestForm()

    return render(request, "base/contact.html", {
        "nav_key": "contact",
        "form": form,
    })