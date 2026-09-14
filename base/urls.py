from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("studio/", views.studio, name="studio"),
    path("donation/", views.donation, name="donation"),
    path("contact/", views.contact, name="contact"),
    path("under-construction/", views.under_construction, name="under_construction"),
]