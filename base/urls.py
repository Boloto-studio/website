from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("blog/<int:pk>/", views.blog_post, name="blog_post"),
    path("studio/", views.studio, name="studio"),
    path("donation/", views.donation, name="donation"),
    path("donation/subscribe/<str:tier_slug>/", views.donation_redirect, name="donation_redirect"),
    path("donation/confirmed/<str:session_id>/", views.donation_confirmed, name="donation_confirmed"),
    path("contact/", views.contact, name="contact"),
    path("under-construction/", views.under_construction, name="under_construction"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]