from django.shortcuts import render, redirect
from django.urls import path
from . import views

app_name = "hosting"

urlpatterns = [
    path("create", views.create_server, name="create"),
    path("success", lambda r: render(r, "hosting/success.html"), name="success"),
]
