"""Root URL configuration for the Center Management project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("activities.api.urls")),
    path("", include("activities.urls")),
]
