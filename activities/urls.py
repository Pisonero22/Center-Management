"""URL patterns for the activities app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Activities
    path("activities/", views.ActivityListView.as_view(), name="activity-list"),
    path("activities/new/", views.ActivityCreateView.as_view(), name="activity-create"),
    path("activities/<int:pk>/", views.ActivityDetailView.as_view(), name="activity-detail"),
    path("activities/<int:pk>/edit/", views.ActivityUpdateView.as_view(), name="activity-update"),
    path("activities/<int:pk>/delete/", views.ActivityDeleteView.as_view(), name="activity-delete"),
    # Enrolments
    path("activities/<int:pk>/enroll/", views.enroll_member, name="activity-enroll"),
    path("activities/<int:pk>/enrollments/", views.activity_enrollments, name="activity-enrollments"),
    path(
        "activities/<int:pk>/enrollments/<int:member_id>/remove/",
        views.remove_enrollment,
        name="enrollment-remove",
    ),
    # Members
    path("members/", views.MemberListView.as_view(), name="member-list"),
    path("members/new/", views.MemberCreateView.as_view(), name="member-create"),
    path("members/<int:pk>/", views.MemberDetailView.as_view(), name="member-detail"),
    path("members/<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member-update"),
    path("members/<int:pk>/delete/", views.MemberDeleteView.as_view(), name="member-delete"),
    # Instructors
    path("instructors/", views.InstructorListView.as_view(), name="instructor-list"),
    path("instructors/new/", views.InstructorCreateView.as_view(), name="instructor-create"),
    path("instructors/<int:pk>/", views.InstructorDetailView.as_view(), name="instructor-detail"),
    path("instructors/<int:pk>/edit/", views.InstructorUpdateView.as_view(), name="instructor-update"),
    path("instructors/<int:pk>/delete/", views.InstructorDeleteView.as_view(), name="instructor-delete"),
    # Rooms
    path("rooms/", views.RoomListView.as_view(), name="room-list"),
    path("rooms/new/", views.RoomCreateView.as_view(), name="room-create"),
    path("rooms/<int:pk>/", views.RoomDetailView.as_view(), name="room-detail"),
    path("rooms/<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room-update"),
    path("rooms/<int:pk>/delete/", views.RoomDeleteView.as_view(), name="room-delete"),
]
