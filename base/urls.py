from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("blog/<int:pk>/", views.blog_post, name="blog_post"),
    path("studio/", views.studio, name="studio"),
    path("donation/", views.donation, name="donation"),
    path("donation/subscribe/<str:tier_slug>/", views.donation_redirect, name="donation_redirect"),
    path("donation/confirmed/<str:session_id>/", views.donation_confirmed, name="donation_confirmed"),
    path("contact/", views.contact, name="contact"),
    # Old gate page; kept as a redirect so bookmarked links don't 404
    path("under-construction/", RedirectView.as_view(pattern_name="home"), name="under_construction"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]