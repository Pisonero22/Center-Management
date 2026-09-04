"""API routes, namespaced under `api:` so they cannot clash with the HTML ones."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router = DefaultRouter()
router.register("activities", views.ActivityViewSet, basename="activity")
router.register("members", views.MemberViewSet)
router.register("instructors", views.InstructorViewSet)
router.register("rooms", views.RoomViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="docs",
    ),
]
