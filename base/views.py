from django.shortcuts import render
from django.utils.translation import gettext as _
from .models import *

# Create your views here.

def home(request):
    hero_posts = HeroPost.objects.all()
    return render(request, "base/home.html", {
        "path_title": _("Home"),
        "events":[1,2,3,4,5,6,7,8],
        "hero_posts":hero_posts,
        "posts":[1,2,3,4,5,6,7,8,9]
    })