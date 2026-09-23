import os
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import random
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from .forms import FrogProfileEditForm, FrogRegistrationForm, WallPostForm
from .models import Frog, FriendRequest

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

def profile_page(request, profile_id=None):
    own_profile = False
    friend_status = ""
    if profile_id:
        if not request.user.is_authenticated:
            return redirect('frogs-login')
        own_profile = profile_id == request.user.id
    else:
        return redirect('frogs-profile', profile_id=request.user.id)
    if own_profile:
        user = request.user
    else:
        try:
            user = User.objects.get(id=profile_id)
            if FriendRequest.objects.filter(from_user=request.user.frog, to_user=user).exists():
                friend_status = "sent"
            elif user.frog.friends.filter(id=request.user.frog.id).exists():
                friend_status = "friends"
        except User.DoesNotExist:
            return render(request, 'frogsnet/profile_not_found.html', status=404)

    frog = user.frog
    modpack_stats = frog.modpack_stats.all() if frog else []

    return render(request, 'frogsnet/profile.html', {
        'profile': frog,
        'activity': frog.status if frog else None,
        'own_profile': own_profile,
        'modpacks': modpack_stats,
        'user_wall': user.wall.posts.order_by('-published_date'),
        'friend_status': friend_status,
        'wall_post_form': WallPostForm(),
        })

@login_required
def friend_request(request, profile_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=profile_id)
        if target_user == request.user:
            return JsonResponse({'error': 'Cannot send a friend request to yourself.'}, status=400)

        existing_request = FriendRequest.objects.filter(from_user=request.user.frog, to_user=target_user).first()
        if existing_request:
            return JsonResponse({'error': 'Friend request already sent.'}, status=400)

        if target_user.frog.friends.filter(id=request.user.frog.id).exists():
            return JsonResponse({'error': 'You are already friends with this user.'}, status=400)

        FriendRequest.objects.create(from_user=request.user.frog, to_user=target_user)
        return JsonResponse({'success': 'Friend request sent.'})
    elif request.method == 'DELETE':
        target_user = get_object_or_404(User, id=profile_id)
        friend_request = FriendRequest.objects.filter(from_user=request.user.frog, to_user=target_user).first()
        if not friend_request:
            return JsonResponse({'error': 'No friend request found to cancel.'}, status=400)

        friend_request.delete()
        return JsonResponse({'success': 'Friend request canceled.'})
    elif request.method == 'PUT':
        target_user = get_object_or_404(User, id=profile_id)
        friend_request = FriendRequest.objects.filter(from_user=target_user.frog, to_user=request.user).first()
        if not friend_request:
            return JsonResponse({'error': 'No friend request found to accept.'}, status=400)

        request.user.frog.friends.add(target_user)
        target_user.frog.friends.add(request.user)
        friend_request.delete()
        return JsonResponse({'success': 'Friend request accepted.'})

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def delete_friend(request, profile_id):
    if request.method == 'DELETE':
        target_user = get_object_or_404(User, id=profile_id)
        frog = request.user.frog
        if not frog.friends.filter(id=target_user.frog.id).exists():
            return JsonResponse({'error': 'You are not friends with this user.'}, status=400)

        frog.friends.remove(target_user)
        return JsonResponse({'success': 'Friend removed.'})

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@login_required
def profile_edit(request):
    user = request.user
    frog = user.frog
    form = FrogProfileEditForm(request.POST or None, request.FILES or None, instance=user, frog=frog)
    original_password_hash = user.password

    if request.method == 'POST' and form.is_valid():
        form.save()
        if user.password != original_password_hash:
            update_session_auth_hash(request, user)
        return redirect('frogs-profile-own')

    return render(request, 'frogsnet/profile_edit.html', {
        'form': form,
        'profile': frog,
        'user': user,
    })


def profile(request, profile_id=None):
    return profile_page(request, profile_id=profile_id)


@login_required
@require_POST
def create_wall_post(request, profile_id):
    target_user = get_object_or_404(User, id=profile_id)
    target_frog = target_user.frog

    if target_user != request.user and not target_frog.allow_external_wall_posts:
        return JsonResponse(
            {'error': str('Wall transmissions are disabled for this profile.')},
            status=403,
        )

    form = WallPostForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    post = form.save(author=request.user, topic=target_user.wall)
    post_html = render_to_string(
        'frogsnet/includes/wall_post.html',
        {'entry': post},
        request=request,
    )
    return JsonResponse(
        {
            'html': post_html,
            'post_id': post.id,
            'count': target_user.wall.posts.count(),
            'content': post.content,
        }
    )