import os
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.db import OperationalError, ProgrammingError
from django.db.models import Max, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import random
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.timesince import timesince
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
import nh3
import markdown2

from base.models import Server
from .forms import ForumPostForm, FrogProfileEditForm, FrogRegistrationForm, WallPostForm
from .models import Frog, FriendRequest, ForumPost, ForumTopic

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
        "description": "Primary survival node. Requires Terminal Zero modpack v1.4. Heavy focus on neurotoxin automation and biome rot.",
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


def _node_state_label(server, load_ratio):
    if not server.is_online:
        return _("OFFLINE // STANDBY"), "offline"
    if load_ratio >= 0.9:
        return _("ONLINE // ALMOST FULL"), "warning"
    return _("ONLINE // FULLY OPERATIONAL"), "online"


def _build_server_node(server, index):
    max_players = max(server.max_players or 0, 1)
    current_players = max(server.current_players or 0, 0)
    load_ratio = min(current_players / max_players, 1)
    status_label, status_tone = _node_state_label(server, load_ratio)

    return {
        "id": server.id,
        "name": server.name,
        "description": server.description or _("No telemetry brief available for this node yet."),
        "ip_address": server.ip_address,
        "connect_address": f"{server.ip_address}:{server.port}",
        "latency_host": server.ip_address,
        "max_players": max_players,
        "current_players": current_players,
        "load_ratio": load_ratio,
        "load_percent": int(round(load_ratio * 100)),
        "slots_left": max(max_players - current_players, 0),
        "is_online": server.is_online,
        "status_label": status_label,
        "status_tone": status_tone,
        "world_size": server.world_size or _("UNKNOWN"),
        "region": server.get_region_display() if server.region else _("UNKNOWN"),
        "modpack_name": server.modpack.name if server.modpack_id else _("UNASSIGNED"),
        "modpack_description": (server.modpack.description if server.modpack_id else "") or _("No modpack briefing synchronized."),
        "modpack_icon": server.modpack.icon_asset_name if server.modpack_id else "echoes_untamed_icon.png",
        "modpack_version": _("v1.0"),
        "node_id": f"BLT-PRIME-{index + 1:02d}",
        "friends_online": (index % 5) + 1,
        "jitter": _("±1.2ms"),
        "uptime_label": _("STABLE_DAEMON") if server.is_online else _("STANDBY"),
    }


@login_required
def servers_list(request):
    search_query = (request.GET.get("q") or "").strip()
    selected_region = (request.GET.get("region") or "ALL").strip().upper()
    selected_modpack = (request.GET.get("modpack") or "ALL").strip()
    online_only = (request.GET.get("online_only") or "0") == "1"
    sort_by = (request.GET.get("sort") or "").strip().lower()

    try:
        servers_qs = Server.objects.select_related("modpack")
        if search_query:
            servers_qs = servers_qs.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(ip_address__icontains=search_query)
                | Q(region__icontains=search_query)
                | Q(modpack__name__icontains=search_query)
                | Q(modpack__description__icontains=search_query)
            )

        valid_regions = {choice[0] for choice in Server.regions}
        if selected_region in valid_regions:
            servers_qs = servers_qs.filter(region=selected_region)
        else:
            selected_region = "ALL"

        if selected_modpack and selected_modpack != "ALL":
            servers_qs = servers_qs.filter(modpack__name=selected_modpack)

        if online_only:
            servers_qs = servers_qs.filter(is_online=True)

        if sort_by in {"population", "population_desc"}:
            sort_by = "population_desc"
            servers_qs = servers_qs.order_by("-current_players", "name")
        elif sort_by == "population_asc":
            servers_qs = servers_qs.order_by("current_players", "name")
        else:
            sort_by = ""
            servers_qs = servers_qs.order_by("-is_featured", "name")

        servers = list(servers_qs)
    except (OperationalError, ProgrammingError):
        servers = []

    nodes = [_build_server_node(server, index) for index, server in enumerate(servers)]
    featured_node = next((node for node, server in zip(nodes, servers) if server.is_featured), None)
    if featured_node is None and nodes:
        featured_node = nodes[0]

    cluster_nodes = [node for node in nodes if not featured_node or node["id"] != featured_node["id"]]
    total_players = sum(node["current_players"] for node in nodes)
    total_capacity = sum(node["max_players"] for node in nodes)
    overall_load = int(round((total_players / total_capacity) * 100)) if total_capacity else 0
    modpacks = sorted({node["modpack_name"] for node in nodes})

    context = {
        "featured_node": featured_node,
        "cluster_nodes": cluster_nodes,
        "total_nodes": len(nodes),
        "online_nodes": sum(1 for node in nodes if node["is_online"]),
        "standby_nodes": sum(1 for node in nodes if not node["is_online"]),
        "total_players": total_players,
        "total_capacity": total_capacity,
        "overall_load": overall_load,
        "modpacks": modpacks,
        "throughput": "98.4MB/s",
        "search_query": search_query,
        "selected_region": selected_region,
        "selected_modpack": selected_modpack,
        "online_only": online_only,
        "sort_by": sort_by,
    }
    return render(request, "frogsnet/servers_list.html", context)


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
        'user_wall': user.wall.posts.order_by('-published_date').filter(response_to=None),
        'friend_status': friend_status,
        'wall_post_form': WallPostForm(),
        })

def _friend_display_name(user):
    frog = getattr(user, 'frog', None)
    if frog is None:
        return user.username

    if frog.show_real_name in {'public', 'squad_only'} and user.first_name:
        return user.first_name

    return user.username


def _friend_card_context(user):
    friend_frog = user.frog
    status = friend_frog.status
    last_seen_display = status['last_online_display'] or 'unknown'
    return {
        'user': user,
        'frog': friend_frog,
        'display_name': _friend_display_name(user),
        'subtitle': friend_frog.location or friend_frog.minecraft_username or '',
        'status': status,
        'avatar_url': friend_frog.avatar.url if friend_frog.avatar else None,
        'last_seen_code': last_seen_display.replace(' ', '_').upper(),
        'profile_name_index': ' '.join([
            _friend_display_name(user),
            user.username,
            friend_frog.location or '',
            friend_frog.minecraft_username or '',
            last_seen_display,
        ]).lower(),
    }


@login_required
def friends_list(request):
    frog = request.user.frog
    search_query = request.GET.get('q', '').strip()

    friends = list(frog.friends.select_related('frog').all())
    friends.sort(key=lambda friend: (
        0 if friend.frog.status['is_active'] or friend.frog.status['in_game_status'] else 1,
        friend.username.lower(),
    ))

    incoming_requests = list(
        FriendRequest.objects.filter(to_user=request.user).select_related('from_user__user').order_by('-created_at')
    )

    friend_cards = []
    for friend in friends:
        friend_cards.append(_friend_card_context(friend))

    grid_cards = friend_cards
    is_search_results = bool(search_query)
    if is_search_results:
        search_users = User.objects.select_related('frog').exclude(id=request.user.id).filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(frog__minecraft_username__icontains=search_query)
            | Q(frog__location__icontains=search_query)
        ).distinct().order_by('username')
        grid_cards = [_friend_card_context(user) for user in search_users]

    request_cards = []
    for incoming_request in incoming_requests:
        source_user = incoming_request.from_user.user
        source_frog = incoming_request.from_user
        request_cards.append({
            'user': source_user,
            'frog': source_frog,
            'display_name': _friend_display_name(source_user),
            'subtitle': source_frog.location or source_frog.minecraft_username or '',
            'received_at': incoming_request.created_at,
            'received_label': timesince(incoming_request.created_at),
            'avatar_url': source_frog.avatar.url if source_frog.avatar else None,
            'profile_name_index': ' '.join([
                _friend_display_name(source_user),
                source_user.username,
                source_frog.location or '',
                source_frog.minecraft_username or '',
            ]).lower(),
        })

    online_count = sum(1 for card in grid_cards if card['status']['is_active'] or card['status']['in_game_status'])

    return render(request, 'frogsnet/friends_list.html', {
        'friend_cards': friend_cards,
        'grid_cards': grid_cards,
        'incoming_requests': request_cards,
        'online_count': online_count,
        'total_count': len(grid_cards),
        'incoming_count': len(request_cards),
        'profile': frog,
        'search_query': search_query,
        'is_search_results': is_search_results,
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
            friend_request = FriendRequest.objects.filter(from_user=target_user.frog, to_user=request.user).first()
        if not friend_request:
            return JsonResponse({'error': 'No friend request found to cancel.'}, status=400)

        friend_request.delete()
        return JsonResponse({'success': 'Friend request canceled.'})
    elif request.method == 'PUT':
        target_user = get_object_or_404(User, id=profile_id)
        friend_request = FriendRequest.objects.filter(from_user=target_user.frog, to_user=request.user).first()
        if not friend_request:
            return JsonResponse({'error': 'No friend request found to accept.'}, status=400)

        request.user.frog.friends.through.objects.get_or_create(
            frog=request.user.frog,
            user=target_user,
        )
        friend_request.delete()
        accepted_friend = _friend_card_context(target_user)
        friend_html = render_to_string('frogsnet/includes/friend_card.html', {'friend': accepted_friend}, request=request)
        return JsonResponse({
            'success': 'Friend request accepted.',
            'friend_html': friend_html,
        })

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def delete_friend(request, profile_id):
    if request.method == 'DELETE':
        target_user = get_object_or_404(User, id=profile_id)
        frog = request.user.frog
        friendship = frog.friends.through.objects.filter(frog=frog, user=target_user).first()
        if friendship is None:
            friendship = frog.friends.through.objects.filter(frog=target_user.frog, user=request.user).first()
        if friendship is None:
            return JsonResponse({'error': 'You are not friends with this user.'}, status=400)

        friendship.delete()
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


@login_required
def forum_new_post(request, topic_id=None):
    topic = None
    if topic_id is not None:
        topic = get_object_or_404(ForumTopic, id=topic_id, owner_if_wall__isnull=True, parent_topic__isnull=True)
    form = ForumPostForm(request.POST or None, forced_topic=topic)

    if request.method == 'POST' and form.is_valid():
        post = form.save(author=request.user)
        return redirect('frogs-forum-thread', post_id=post.id)

    return render(request, 'frogsnet/forum_new_post.html', {
        'form': form,
        'topic': topic,
    })


def forum_index(request):
    search_query = (request.GET.get('q') or '').strip()
    topics = (
        ForumTopic.objects
        .filter(parent_topic__isnull=True, owner_if_wall__isnull=True)
        .annotate(latest_post=Max('posts__published_date'))
        .order_by('-is_pinned', '-latest_post', 'title')
    )

    if search_query:
        topics = topics.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(posts__title__icontains=search_query)
            | Q(posts__content__icontains=search_query)
        ).distinct()

    topic_sections = []
    for topic in topics:
        posts = topic.posts.select_related('author').filter(response_to__isnull=True).order_by('-published_date')
        if search_query:
            posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
        topic_sections.append({
            'topic': topic,
            'posts': list(posts[:3]),
            'total_posts': posts.count(),
        })

    return render(request, 'frogsnet/forum_index.html', {
        'topic_sections': topic_sections,
        'search_query': search_query,
    })


def forum_topic(request, topic_id):
    topic = get_object_or_404(ForumTopic, id=topic_id, owner_if_wall__isnull=True)
    search_query = (request.GET.get('q') or '').strip()

    posts = topic.posts.select_related('author').filter(response_to__isnull=True).order_by('-published_date')
    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    subtopics = topic.subtopics.select_related('parent_topic').order_by('title').all()

    return render(request, 'frogsnet/forum_topic.html', {
        'topic': topic,
        'page_obj': page_obj,
        'search_query': search_query,
        'subtopics': subtopics,
    })


def forum_topic_redirect(request, topic_id):
    topic = get_object_or_404(ForumTopic, id=topic_id, owner_if_wall__isnull=True, parent_topic__isnull=True)
    return redirect('frogs-forum-topic', topic_id=topic.id)


def forum_thread(request, post_id):
    root_post = get_object_or_404(ForumPost, id=post_id)
    topic = root_post.topic

    if request.method == 'POST' and request.user.is_authenticated:
        content = (request.POST.get('content') or '').strip()
        if content:
            response_to = root_post
            quoted_id = request.POST.get('response_to')
            quoted_post = None
            if quoted_id:
                quoted_post = topic.posts.filter(id=quoted_id).first()
                response_to = quoted_post or root_post
                if quoted_post is not None:
                    quoted_lines = quoted_post.content.strip().splitlines() or [quoted_post.content.strip()]
                    quote_block = "\n".join(f"> {line}" if line else ">" for line in quoted_lines)
                    content = f"{quote_block}\n\n{content}"
            ForumPost.objects.create(
                author=request.user,
                topic=topic,
                response_to=response_to,
                content=content,
                title=Truncator(content).chars(60),
            )
            return redirect(f"{request.path}?page=last")

    def collect_replies(post):
        replies = []
        for reply in post.responses.select_related('author').order_by('published_date'):
            replies.append(reply)
            replies.extend(collect_replies(reply))
        return replies

    all_replies = collect_replies(root_post)

    paginator = Paginator(all_replies, 10)
    page_number = request.GET.get('page', 1)
    if page_number == 'last':
        page_number = paginator.num_pages or 1
    page_obj = paginator.get_page(page_number)

    quote_id = request.GET.get('quote')
    quoted_post = None
    if quote_id:
        quoted_post = topic.posts.filter(id=quote_id).select_related('author').first()

    reply_target = quoted_post or (page_obj.object_list[0] if page_obj.object_list else None)
    if request.user.is_authenticated:
        root_post.upvoted = root_post.upvotes.filter(id=request.user.id).exists()
    else:
        root_post.upvoted = False

    for reply in page_obj.object_list:
        reply.upvoted = request.user.is_authenticated and reply.upvotes.filter(id=request.user.id).exists()

    return render(request, 'frogsnet/forum_thread.html', {
        'topic': topic,
        'root_post': root_post,
        'page_obj': page_obj,
        'page_number': page_obj.number,
        'quoted_post': quoted_post,
        'reply_target': reply_target,
        'reply_count': len(all_replies),
        'total_pages': paginator.num_pages,
        'can_reply': request.user.is_authenticated,
    })


@login_required
@require_POST
def forum_thread_upvote(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    was_upvoted = request.user in post.upvotes.all()
    if was_upvoted:
        post.upvotes.remove(request.user)
    else:
        post.upvotes.add(request.user)
    upvoted = request.user in post.upvotes.all()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'upvoted': upvoted,
            'count': post.upvotes.count(),
        })

    next_url = request.POST.get('next') or (f"/frogs/forum/post/{post.id}/" if post.id else '/frogs/')
    return redirect(next_url)


@login_required
@require_POST
def forum_thread_close(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if post.author_id != request.user.id:
        return redirect('frogs-forum-thread', post_id=post.id)

    post.is_open = False
    post.save(update_fields=['is_open'])
    next_url = request.POST.get('next') or reverse('frogs-forum-thread', args=[post.id])
    return redirect(next_url)


@login_required
@require_POST
def forum_thread_reopen(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if post.author_id != request.user.id:
        return redirect('frogs-forum-thread', post_id=post.id)

    post.is_open = True
    post.save(update_fields=['is_open'])
    next_url = request.POST.get('next') or reverse('frogs-forum-thread', args=[post.id])
    return redirect(next_url)


@login_required
@require_POST
def forum_thread_delete(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if post.author_id != request.user.id:
        return redirect('frogs-forum-thread', post_id=post.id)

    topic_id = post.topic_id
    next_url = "/" or request.POST.get('next') or reverse('frogs-forum-topic', args=[topic_id])
    post.delete()
    return redirect(next_url)


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

@login_required
@require_POST
def generate_post_preview(request):
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'No content provided.'}, status=400)

    preview_html = nh3.clean(markdown2.markdown(content))
    return JsonResponse({'html': preview_html})