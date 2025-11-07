from .models import Event
from django.shortcuts import render
from django.utils.translation import gettext as _

# Create your views here.


def home(request):
    events = Event.objects.all()  # Fetch all events from the database
    return render(request, "base/home.html", {
        "path_title": _("Home"),
        "events": events,
        "posts": [1, 2, 3, 4, 5, 6, 7, 8, 9]
    })
