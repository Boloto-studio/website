from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path("register/", views.register, name="register"),
    path("", RedirectView.as_view(url="register/", permanent=True), name="frogsnet-home"),
]