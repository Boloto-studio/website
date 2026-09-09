from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.db.utils import OperationalError, ProgrammingError

from .forms import ContactRequestForm
from .models import BlogPost, Event, HeroSlide, StaffMember

DEFAULT_HERO_SLIDES = [
    {
        "sector": "SECTOR 7",
        "title": "PROJECT: SWAMP",
        "subtitle": "The flagship modpack for hardcore survival. Enter the swamp. Toxic environments, hostile fauna, and scarce resources await.",
        "image": "https://images.unsplash.com/photo-1542261777448-23d2a287091c?q=80&w=2000&auto=format&fit=crop",
        "link": "#terminal-logs",
        "link_text": "ACCESS_FILES",
    },
    {
        "sector": "SECTOR 4",
        "title": "PROJECT: WASTELAND",
        "subtitle": "Irradiated deserts and ruined megacities. Scavenge for parts, build your rig, and survive the harsh solar storms.",
        "image": "https://images.unsplash.com/photo-1614729939124-032f0b56c9ce?q=80&w=2000&auto=format&fit=crop",
        "link": "#terminal-logs",
        "link_text": "ACCESS_FILES",
    },
    {
        "sector": "SECTOR 9",
        "title": "PROJECT: NEON DISTRICT",
        "subtitle": "Cybernetic enhancements and corporate espionage. Infiltrate the megacorps in this vertical, rain-slicked concrete jungle.",
        "image": "https://images.unsplash.com/photo-1605806616949-1e87b487cb2a?q=80&w=2000&auto=format&fit=crop",
        "link": "#terminal-logs",
        "link_text": "ACCESS_FILES",
    },
]

DEFAULT_STAFF_PROFILES = [
    {
        "callsign": "Vektor",
        "name": "Viktor Volkov",
        "role": "LEAD_ENGINEER",
        "bio": "Mastermind behind the core logic systems. Specializes in terrain generation and structural decay algorithms.",
        "status": "ONLINE",
        "internal_code": "BLT-001",
        "photo_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCJ1lFW-ymLDawC6JqXeYTLqq_VzV8d9hsrF6CLFrKfOu9176mSYbLphQogV5-6Ob1W6AIZKL-6OvlqAvS__2UjsRmBLgm79PWCzGoVuF-GdvHFUMwFU0RjlZEziKMovKeQiIb-ee_0MVky9GZCr6KpNKMN50zK44csiec9-_-DW6SocwpspOLPRuLpzQFPnKex3VAw462bPmY7nMdLAZ63DmL_-I0U-uY5qBhUoPBiei8tt6_PxYNTknEsaH8Q65Fzucg8-YyDWvMS",
        "links": [
            {"label": "X", "url": ""},
            {"label": "GitHub", "url": ""},
            {"label": "Portfolio", "url": ""},
        ],
    },
    {
        "callsign": "Cipher",
        "name": "Elena Rossi",
        "role": "ART_DIRECTOR",
        "bio": "Dictates the visual decay. Responsible for all textures, models, and the overarching Swamp Lab aesthetic.",
        "status": "AWAY",
        "internal_code": "BLT-002",
        "photo_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDmUoGq_VwPdYPEBhkuVJwX1UF9gYEf0CIhFOZeL78rj6PmlfPKIxw_l5hdq5eFJM0Mc-WOV4mDZfNGPIxAYUrtuCzzYDqEs1i_464ccujWsX9zRbam1JhKWQnD1t9Bn0_nnZU7q1pXc9BZpuRlaZa6hn_TwfPFjSnpggHzFF7m12wNhIasCbjZmw2y-h6CAUi0qWTW9tVGQnlVY6tMciAZAOlREA1hAQidtCHwbzNCMZ0eIsXipCZZhwpxAbbb8Cr_y00Zzp0cPrNL",
        "links": [
            {"label": "X", "url": ""},
            {"label": "GitHub", "url": ""},
            {"label": "Portfolio", "url": ""},
        ],
    },
    {
        "callsign": "Static",
        "name": "Marcus Thorne",
        "role": "COMMS_OFFICER",
        "bio": "Manages the external arrays. Handles community transmissions, server logistics, and bug report triaging.",
        "status": "ONLINE",
        "internal_code": "BLT-003",
        "photo_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBtKZzIDk6LzvJVvOuIYHNFgaL2HFkWkBL3-IDNud15W1CKEdMGHoplB7MjC9T_anbWYuyxa6DPdVDdXyZ5vXLq5UC0Irk1ApVnMLhONia_KM_dHop3KugEX2rQUGVOYM0mizpvFEWL1-1EuqvQoFaNf9V8N6wlbBU8vLZUHjITKMbgzxhw8YGvtCroKkNhKZETON7rsHo_T7PWfgQVZGWU_ECwqnBzgSB2RxphyPO65L6sUtgfXiUj_twcJOZ7vDh2vOX4TBq88ldl",
        "links": [
            {"label": "X", "url": ""},
            {"label": "GitHub", "url": ""},
            {"label": "Portfolio", "url": ""},
        ],
    },
]

DONATION_PROGRESS = {
    "percent": 80,
    "target": "$500/MO",
    "display": "████████░░",
}

DONATION_TIERS = [
    {
        "name": "SCAVENGER",
        "price": "$5",
        "interval": "/ MONTH",
        "features": ["Discord Role", "Early Updates"],
        "button_text": "SELECT_SCAVENGER.SH",
        "featured": False,
        "link": "",
    },
    {
        "name": "OPERATIVE",
        "price": "$15",
        "interval": "/ MONTH",
        "features": ["Discord Role", "Early Updates", "Beta Server Access"],
        "button_text": "SELECT_OPERATIVE.SH",
        "featured": True,
        "featured_label": "THE MIDDLE ONE",
        "link": "",
    },
    {
        "name": "OVERSEER",
        "price": "$30",
        "interval": "/ MONTH",
        "features": ["Discord Role", "Early Updates", "Beta Server Access", "Hall of Fame"],
        "button_text": "SELECT_OVERSEER.SH",
        "featured": False,
        "link": "",
    },
]


def _get_hero_slides():
    try:
        slides = list(HeroSlide.objects.filter(is_active=True).order_by("order", "-created_at"))
    except (OperationalError, ProgrammingError):
        slides = []

    if not slides:
        return DEFAULT_HERO_SLIDES

    return [
        {
            "sector": f"SECTOR {index + 1}",
            "title": slide.title,
            "subtitle": slide.subtitle,
            "image": slide.image,
            "link": slide.link or "#terminal-logs",
            "link_text": slide.link_text or "ACCESS_FILES",
        }
        for index, slide in enumerate(slides)
    ]


def _build_terminal_entries(posts, events):
    entries = []

    for post in posts:
        entries.append(
            {
                "published": post.published_date,
                "date_label": timezone.localtime(post.published_date).strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "TEXT_LOG",
                "title": post.title,
                "description": Truncator(post.content).chars(170),
                "action_text": "READ_FULL_LOG",
                "action_icon": "arrow_forward",
                "action_url": "#",
                "thumbnail": "",
                "runtime": "",
            }
        )

    for event in events:
        thumbnail = ""
        runtime = ""
        is_media = bool(event.youtube_video_id or event.link)
        if event.youtube_video_id:
            thumbnail = f"https://i.ytimg.com/vi/{event.youtube_video_id}/hqdefault.jpg"
            runtime = "LIVE"

        entries.append(
            {
                "published": event.date,
                "date_label": timezone.localtime(event.date).strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "MEDIA_FILE" if is_media else "TEXT_LOG",
                "title": event.title,
                "description": Truncator(event.description).chars(170),
                "action_text": "PLAY_TRANSMISSION" if is_media else "READ_FULL_LOG",
                "action_icon": "play_circle" if is_media else "arrow_forward",
                "action_url": event.link or "#",
                "thumbnail": thumbnail,
                "runtime": runtime,
            }
        )

    entries.sort(key=lambda entry: entry["published"], reverse=True)
    return entries[:4]


def _build_staff_profiles():
    try:
        staff = list(StaffMember.objects.all())
    except (OperationalError, ProgrammingError):
        staff = []

    if not staff:
        return DEFAULT_STAFF_PROFILES

    profiles = []
    for index, member in enumerate(staff):
        fallback = DEFAULT_STAFF_PROFILES[index % len(DEFAULT_STAFF_PROFILES)]
        photo_url = member.photo.url if member.photo else fallback["photo_url"]
        profiles.append(
            {
                "callsign": member.callsign or fallback["callsign"],
                "name": member.name,
                "role": member.role.replace(" ", "_").upper(),
                "bio": member.bio or fallback["bio"],
                "status": member.get_status_display().upper(),
                "internal_code": member.internal_code or f"BLT-{index + 1:03d}",
                "photo_url": photo_url,
                "links": [
                    {"label": "X", "url": member.x_url or ""},
                    {"label": "GitHub", "url": member.github_url or ""},
                    {"label": "Portfolio", "url": member.portfolio_url or ""},
                ],
            }
        )

    return profiles


def home(request):
    try:
        events = Event.objects.all().order_by("-date")[:6]
        blog_counts = BlogPost.objects.count()
        blog_posts = BlogPost.objects.all().order_by("-published_date")[:8]
    except (OperationalError, ProgrammingError):
        events = []
        blog_counts = 0
        blog_posts = []

    return render(
        request,
        "base/home.html",
        {
            "hero_slides": _get_hero_slides(),
            "terminal_entries": _build_terminal_entries(blog_posts, events),
            "extra_blogs": blog_counts > 8,
        },
    )


def studio(request):
    return render(
        request,
        "base/studio.html",
        {
            "mission_directory": "DIR: /usr/local/boloto/team",
            "mission_log": [
                "INITIALIZING BOLOTO PROTOCOL...",
                "ESTABLISHED: 2021",
                "DIRECTIVE: Engineer uncompromising, lore-dense modifications for the Minecraft ecosystem.",
                "We are a collective of architects, coders, and digital scavengers operating from the Swamp Lab.",
                "Our flagship project, PROJECT: SWAMP, is an aggressive reimagining of survival mechanics set against industrial decay and environmental hostility.",
                "We build tools for those who find vanilla environments too hospitable.",
                "END LOG_",
            ],
            "staff_profiles": _build_staff_profiles(),
        },
    )


def donation(request):
    return render(
        request,
        "base/donation.html",
        {
            "donation_progress": DONATION_PROGRESS,
            "donation_tiers": DONATION_TIERS,
        },
    )


def contact(request):
    submitted = request.GET.get("submitted") == "1"
    form = ContactRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"{reverse('contact')}?submitted=1")

    return render(
        request,
        "base/contact.html",
        {
            "form": form,
            "submitted": submitted,
        },
    )


def team(request):
    return studio(request)