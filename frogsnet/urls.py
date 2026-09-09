from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="frogs-register"),
    path("login/", views.login_view, name="frogs-login"),
    path("forum/", views.forum_index, name="frogs-forum"),
    path("forum/new/", views.forum_new, name="frogs-forum-new"),
    path("forum/thread/", views.forum_thread, name="frogs-forum-thread"),
    path("profile/", views.profile, name="frogs-profile"),
    path("friends/", views.friends, name="frogs-friends"),
    path("servers/", views.servers, name="frogs-servers"),
    path("", views.home, name="frogsnet-home"),
]