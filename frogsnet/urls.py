from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="frogs-register"),
    path("login/", views.login_view, name="frogs-login"),
    path("profile/edit/", views.profile_edit, name="frogs-profile-edit"),
    path("profile/", views.profile_page, name="frogs-profile-own"),
    path("friends/", views.friends_list, name="frogs-friends"),
    path("profile/<int:profile_id>/wall-posts/", views.create_wall_post, name="frogs-wall-post-create"),
    path("profile/<int:profile_id>/", views.profile_page, name="frogs-profile"),
    path("profile/<int:profile_id>/friend-request/", views.friend_request, name="frogs-friend-request"),
    path("profile/<int:profile_id>/delete-friend/", views.delete_friend, name="frogs-friend-delete"),
    path("", views.home, name="frogsnet-home"),
]