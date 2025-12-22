import os
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
import random

# Create your views here.

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or login page after registration
        return render(request, "frogsnet/register.html", {"form": form})
    else:
        background_images = []
        backgrounds_path = os.path.join(settings.BASE_DIR, "frogsnet", "static", "frogsnet", "backgrounds")
        try:
            if os.path.exists(backgrounds_path):
                background_images = os.listdir(backgrounds_path)
        except OSError:
            pass  # Handle case where directory doesn't exist or can't be read
        form = UserCreationForm()
        bg_image = random.choice(background_images) if background_images else None
        return render(request, "frogsnet/register.html", {"form": form, "bg": bg_image})