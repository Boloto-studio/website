from django.urls import path

from . import views

app_name = "modpacks"

urlpatterns = [
    path("clients/", views.register_client, name="register_client"),
    path("modpacks/", views.modpack_list, name="modpack_list"),
    path("modpacks/<slug:slug>/", views.modpack_detail, name="modpack_detail"),
    path("keys/redeem/", views.redeem, name="redeem_key"),
]
