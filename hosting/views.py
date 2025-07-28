# hosting/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import requests
from .forms import ServerCreationForm
from .models import ServerInstance

CRAFTY_API_URL = "https://crafty.boloto.studio/api/v2/servers"
CRAFTY_TOKEN = "<your_crafty_token>"  # Store this securely!

# @login_required
def create_server(request):
    if request.method == "POST":
        form = ServerCreationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            ram_min = form.cleaned_data["ram_min"]
            ram_max = form.cleaned_data["ram_max"]

            payload = {
                "name": name,
                "monitoring_type": "minecraft_java",
                "minecraft_java_monitoring_data": {
                    "host": "127.0.0.1",
                    "port": 25565
                },
                "create_type": "minecraft_java",
                "minecraft_java_create_data": {
                    "create_type": "download_jar",
                    "download_jar_create_data": {
                        "type": "Vanilla",
                        "version": "1.20.1",  # or latest
                        "mem_min": ram_min,
                        "mem_max": ram_max,
                        "server_properties_port": 25565,
                        "agree_to_eula": True
                    }
                }
            }

            headers = {
                "Authorization": f"Bearer {CRAFTY_TOKEN}"
            }

            response = requests.post(CRAFTY_API_URL, json=payload, headers=headers)
            data = response.json()

            if response.ok and data["status"] == "ok":
                ServerInstance.objects.create(
                    user=request.user,
                    name=name,
                    ram_min=ram_min,
                    ram_max=ram_max,
                    crafty_server_id=data["data"]["new_server_id"],
                    crafty_uuid=data["data"]["new_server_uuid"]
                )
                return redirect("hosting:success")
            else:
                form.add_error(None, "Failed to create server. Try again.")

    else:
        form = ServerCreationForm()

    return render(request, "hosting/create_server.html", {"form": form})
