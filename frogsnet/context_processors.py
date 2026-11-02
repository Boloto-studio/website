from .models import FriendRequest


def friend_requests(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'pending_friend_requests': 0}
    return {'pending_friend_requests': FriendRequest.objects.filter(to_user=user).count()}
