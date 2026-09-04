"""Views for the cultural centre.

Class-based views cover the repetitive CRUD for the four entities; the
enrolment flow is written as plain function views because it is the part with
actual business rules.

Browsing is open to anyone; every view that writes to the database requires an
authenticated user.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ActivityForm, EnrollmentForm, InstructorForm, MemberForm, RoomForm
from .models import Activity, Enrollment, Instructor, Member, Room


class HomeView(TemplateView):
    template_name = "home.html"


# --------------------------------------------------------------------------
# Activities
# --------------------------------------------------------------------------
class ActivityListView(ListView):
    model = Activity
    template_name = "activities/list.html"
    context_object_name = "activities"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("instructor", "main_room")
            .annotate(enrollment_count=Count("enrollments"))
            # annotate() adds a GROUP BY, which drops Meta.ordering and would
            # make pagination non-deterministic, so ordering is restated here.
            .order_by("starts_at")
        )
        category = self.request.GET.get("category")
        instructor_id = self.request.GET.get("instructor")

        if category:
            queryset = queryset.filter(category=category)
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instructors"] = Instructor.objects.all()
        context["categories"] = Activity.Category.choices
        return context


class ActivityDetailView(DetailView):
    model = Activity
    template_name = "activities/detail.html"
    context_object_name = "activity"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("instructor", "main_room")
            .prefetch_related("secondary_rooms", "members")
        )


class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = "activities/form.html"
    success_url = reverse_lazy("activity-list")


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = "activities/form.html"
    success_url = reverse_lazy("activity-list")


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = "activities/confirm_delete.html"
    success_url = reverse_lazy("activity-list")


# --------------------------------------------------------------------------
# Enrolments
# --------------------------------------------------------------------------
@login_required
def enroll_member(request, pk):
    """Enrol a member in an activity, respecting its capacity."""
    activity = get_object_or_404(Activity, pk=pk)

    if request.method == "POST":
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data["member"]
            # Two people can hit "Enrol" for the last place at the same time,
            # so the count and the insert happen inside one transaction. The
            # row lock is a no-op on SQLite but does the work on PostgreSQL.
            with transaction.atomic():
                locked = Activity.objects.select_for_update().get(pk=activity.pk)
                if locked.is_full:
                    places = "place" if locked.capacity == 1 else "places"
                    messages.error(
                        request,
                        f"{locked.name} is full ({locked.capacity} {places}).",
                    )
                else:
                    _, created = Enrollment.objects.get_or_create(
                        activity=locked, member=member
                    )
                    if created:
                        messages.success(request, f"{member} is now enrolled.")
                    else:
                        messages.info(request, f"{member} was already enrolled.")
            return redirect("activity-enrollments", pk=pk)
    else:
        form = EnrollmentForm()

    return render(
        request,
        "activities/enroll.html",
        {"form": form, "activity": activity},
    )


def activity_enrollments(request, pk):
    """List everyone enrolled in an activity."""
    activity = get_object_or_404(Activity, pk=pk)
    enrollments = activity.enrollments.select_related("member")

    return render(
        request,
        "activities/enrollments.html",
        {"activity": activity, "enrollments": enrollments},
    )


@login_required
@require_POST
def remove_enrollment(request, pk, member_id):
    """Remove a member from an activity. POST only: it changes state."""
    activity = get_object_or_404(Activity, pk=pk)
    deleted, _ = Enrollment.objects.filter(
        activity=activity, member_id=member_id
    ).delete()
    if deleted:
        messages.success(request, "Enrolment removed.")

    return redirect("activity-enrollments", pk=pk)


# --------------------------------------------------------------------------
# Members
# --------------------------------------------------------------------------
class MemberListView(ListView):
    model = Member
    template_name = "members/list.html"
    context_object_name = "members"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        activity_id = self.request.GET.get("activity")

        if activity_id:
            queryset = queryset.filter(enrollments__activity_id=activity_id).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activities"] = Activity.objects.all()
        return context


class MemberDetailView(DetailView):
    model = Member
    template_name = "members/detail.html"
    context_object_name = "member"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("activities")


class MemberCreateView(LoginRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = "members/form.html"
    success_url = reverse_lazy("member-list")


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = "members/form.html"
    success_url = reverse_lazy("member-list")


class MemberDeleteView(LoginRequiredMixin, DeleteView):
    model = Member
    template_name = "members/confirm_delete.html"
    success_url = reverse_lazy("member-list")


# --------------------------------------------------------------------------
# Instructors
# --------------------------------------------------------------------------
class InstructorListView(ListView):
    model = Instructor
    template_name = "instructors/list.html"
    context_object_name = "instructors"
    paginate_by = 10


class InstructorDetailView(DetailView):
    model = Instructor
    template_name = "instructors/detail.html"
    context_object_name = "instructor"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("activities")


class InstructorCreateView(LoginRequiredMixin, CreateView):
    model = Instructor
    form_class = InstructorForm
    template_name = "instructors/form.html"
    success_url = reverse_lazy("instructor-list")


class InstructorUpdateView(LoginRequiredMixin, UpdateView):
    model = Instructor
    form_class = InstructorForm
    template_name = "instructors/form.html"
    success_url = reverse_lazy("instructor-list")


class InstructorDeleteView(LoginRequiredMixin, DeleteView):
    model = Instructor
    template_name = "instructors/confirm_delete.html"
    success_url = reverse_lazy("instructor-list")


# --------------------------------------------------------------------------
# Rooms
# --------------------------------------------------------------------------
class RoomListView(ListView):
    model = Room
    template_name = "rooms/list.html"
    context_object_name = "rooms"
    paginate_by = 10


class RoomDetailView(DetailView):
    model = Room
    template_name = "rooms/detail.html"
    context_object_name = "room"

    def get_queryset(self):
        return super().get_queryset().select_related("manager")


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/form.html"
    success_url = reverse_lazy("room-list")


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/form.html"
    success_url = reverse_lazy("room-list")


class RoomDeleteView(LoginRequiredMixin, DeleteView):
    model = Room
    template_name = "rooms/confirm_delete.html"
    success_url = reverse_lazy("room-list")
