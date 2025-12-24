from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("studio/", views.studio, name="studio"),
    path("team/", views.team, name="team"),
]