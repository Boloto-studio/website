import os
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
import random

from .forms import FrogRegistrationForm
from .models import Frog

# Create your views here.


SERVER_METRICS = [
    {"label": "TOTAL ACTIVE NODES", "value": "03", "suffix": ""},
    {"label": "CONCURRENT USERS", "value": "142", "suffix": "/ 500"},
    {"label": "GLOBAL COMPUTE LOAD", "value": "78", "suffix": "%"},
]

SERVER_LIST = [
    {
        "name": "SWAMPY ALPHA [MODDED]",
        "status": "STABLE",
        "description": "Primary survival node. Requires Terminal Zero modpack v1.4. Heavy focus on neurotoxel automation and biome rot.",
        "ip": "alpha.swampy.net",
        "players": "112 / 200",
        "version": "TZ_v1.2.4",
        "ping": "18ms",
    },
    {
        "name": "WASTELAND PVP",
        "status": "HIGH LOAD",
        "description": "Unregulated combat zone. No safe codes. Proceed with extreme caution. Weekly wipes.",
        "ip": "pvp.swampy.net",
        "players": "89 / 100",
        "version": "TZ_v1.2.4",
        "ping": "86ms",
    },
    {
        "name": "LEGACY ARCHIVE",
        "status": "OFFLINE",
        "description": "Read-only mirror of retired event logs and discontinued modpack builds.",
        "ip": "archive.swampy.net",
        "players": "00 / 100",
        "version": "TZ_v0.7.3",
        "ping": "--",
    },
]

FRIENDS_LIST = [
    {"name": "CYBER_HOUND", "level": 42, "clan": "HOWL", "status": "ONLINE", "note": "MATCH: SECTOR_7", "icon": "pets"},
    {"name": "GLITCH_MECH", "level": 89, "clan": "VOID", "status": "ONLINE", "note": "IDLE: DIGITAL_BASTION", "icon": "construction"},
    {"name": "USER_9942", "level": 12, "clan": "MORSE", "status": "ONLINE", "note": "ENGAGED: FORUMS", "icon": "person"},
    {"name": "DEAD_DROP", "level": 77, "clan": "NULL", "status": "AWAY", "note": "LAST_SEEN: 48_HOURS_AGO", "icon": "skull"},
    {"name": "STAR_DUST", "level": 55, "clan": "NOVA", "status": "OFFLINE", "note": "LAST_SEEN: 8_DAYS_AGO", "icon": "flare"},
]

DEFAULT_PROFILE = {
    "callsign": "GHOST_IN_THE_SHELL",
    "identity": "ID Motoko Kusanagi",
    "clan": "BOGWITCH_SENTINEL",
    "status": "ACTIVE",
    "avatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCJ1lFW-ymLDawC6JqXeYTLqq_VzV8d9hsrF6CLFrKfOu9176mSYbLphQogV5-6Ob1W6AIZKL-6OvlqAvS__2UjsRmBLgm79PWCzGoVuF-GdvHFUMwFU0RjlZEziKMovKeQiIb-ee_0MVky9GZCr6KpNKMN50zK44csiec9-_-DW6SocwpspOLPRuLpzQFPnKex3VAw462bPmY7nMdLAZ63DmL_-I0U-uY5qBhUoPBiei8tt6_PxYNTknEsaH8Q65Fzucg8-YyDWvMS",
    "modpacks": [
        {"icon": "deployed_code", "name": "Project: Swamp"},
        {"icon": "shield", "name": "Bog Protocol"},
        {"icon": "build", "name": "Wasteland Relay"},
        {"icon": "directions_car", "name": "Road_Core"},
        {"icon": "camping", "name": "Lanternkeeper"},
    ],
    "squad": ["BATOU_98", "TOGUSA_MA51", "ISHIKAWA_NET", "SATO_SN1PE"],
    "history": [
        {"log": "LOG_ID: 0003.1", "time": "7_MINUTES_AGO", "text": "Secured the perimeter around Sector 4. Encountered minimal resistance, but comms signal degradation was severe. Proceeding with caution. Need backup on the freeway."},
        {"log": "LOG_ID: 0481.C", "time": "T-MINUS 12_HOURS", "text": "Initial recon of the abandoned facility complete. Found traces of old world tech. Uploading schematics to main frame. Awaiting further instructions."},
    ],
}

FORUM_SECTIONS = [
    {
        "directory": "/NEWS",
        "threads": [
            {
                "prefix": "[ANNOUNCEMENT]",
                "title": "V0.8.4 PATCH NOTES & KNOWN ISSUES",
                "author": "SYS_ADMIN",
                "timestamp": "T-MINUS 21:06:00",
                "replies": "1,684",
                "views": "8.6K",
            }
        ],
    },
    {
        "directory": "/TECH_SUPPORT",
        "threads": [
            {
                "prefix": "[ERROR_REPORT]",
                "title": "OPTIMIZING SCANLINE RENDERER IN WEBGL",
                "author": "NULL_POINTER",
                "timestamp": "02_HOURS_AGO",
                "replies": "428",
                "views": "31.2K",
            }
        ],
    },
]

THREAD_DETAIL = {
    "breadcrumb": "/BIN/FORUM/TECH_SUPPORT/THREAD_99482",
    "title": "OPTIMIZING SCANLINE RENDERER IN WEBGL",
    "author": "NULL_POINTER",
    "timestamp": "02_HOURS_AGO",
    "body": [
        "Encountering severe frame drops when applying the primary scanline shader over a complex geometry scene.",
        "The current implementation utilizes a fragment shader calculating distortion per pixel, causing a massive GPU bottleneck.",
        "Is there a more hardware-efficient method to achieve the same visual degradation without stalling the pipeline?",
        "Requesting immediate technical intervention.",
    ],
    "replies": [
        {"author": "SYS_ADMIN", "timestamp": "T-MINUS 01_HOUR", "text": "Event log patch queued. Avoid inline trig functions inside the distortion pass and move scanline variance into a low-resolution LUT."},
        {"author": "VEKTOR", "timestamp": "T-MINUS 38_MIN", "text": "Confirmed. We offloaded the barrel distortion to vertex space on the prototype branch and frame time normalized instantly."},
    ],
}


def home(request):
    if request.user.is_authenticated:
        return redirect('frogs-forum')
    return redirect('frogs-login')

def register(request):
    if request.user.is_authenticated:
        return redirect('frogs-forum')

    form = FrogRegistrationForm(request.POST or None)
    background_images = []
    backgrounds_path = os.path.join(settings.BASE_DIR, "frogsnet", "static", "frogsnet", "backgrounds")
    try:
        if os.path.exists(backgrounds_path):
            background_images = os.listdir(backgrounds_path)
    except OSError:
        pass

    bg_image = random.choice(background_images) if background_images else None
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"{request.path.rsplit('/', 2)[0]}/login/?created=1")

    return render(
        request,
        "frogsnet/register.html",
        {
            "form": form,
            "background_image": bg_image,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('frogs-forum')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect('frogs-forum')

    return render(
        request,
        'frogsnet/login.html',
        {
            'form': form,
            'created': request.GET.get('created') == '1',
        },
    )


def forum_index(request):
    return render(
        request,
        'frogsnet/forum_list.html',
        {
            'sections': FORUM_SECTIONS,
        },
    )


def forum_new(request):
    if request.method == 'POST':
        return redirect(f"{request.path}?submitted=1")

    return render(
        request,
        'frogsnet/forum_new.html',
        {
            'submitted': request.GET.get('submitted') == '1',
            'topic_options': ['/NEWS', '/TECH_SUPPORT', '/DEVLOG', '/ARCHIVE'],
        },
    )


def forum_thread(request):
    return render(
        request,
        'frogsnet/forum_thread.html',
        {
            'thread': THREAD_DETAIL,
        },
    )


def profile(request):
    if request.user.is_authenticated and hasattr(request.user, 'frog'):
        frog = request.user.frog
        profile_data = {
            'callsign': request.user.username.upper(),
            'identity': f"ID {frog.minecraft_username or request.user.get_full_name() or request.user.username}",
            'clan': 'BOGWITCH_SENTINEL',
            'status': frog.get_status_display().upper(),
            'avatar': frog.avatar or DEFAULT_PROFILE['avatar'],
            'modpacks': DEFAULT_PROFILE['modpacks'],
            'squad': DEFAULT_PROFILE['squad'],
            'history': DEFAULT_PROFILE['history'],
        }
    else:
        profile_data = DEFAULT_PROFILE

    return render(
        request,
        'frogsnet/profile.html',
        {
            'profile': profile_data,
        },
    )


def friends(request):
    return render(
        request,
        'frogsnet/friends.html',
        {
            'friends_list': FRIENDS_LIST,
        },
    )


def servers(request):
    return render(
        request,
        'frogsnet/servers.html',
        {
            'server_metrics': SERVER_METRICS,
            'server_list': SERVER_LIST,
        },
    )