from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("studio/", views.studio, name="studio"),
    path("donation/", views.donation, name="donation"),
    path("contact/", views.contact, name="contact"),
    path("team/", views.team, name="team"),
]