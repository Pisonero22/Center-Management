"""Viewsets for the REST API.

The permissions, the filters and the enrolment rules are the same ones the HTML
side uses: reading is public, writing needs an account, and enrolling goes
through `activities.services`.
"""

from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from .. import services
from ..models import Activity, Instructor, Member, Room
from .serializers import (
    ActivitySerializer,
    EnrollmentCreateSerializer,
    EnrollmentSerializer,
    InstructorSerializer,
    MemberSerializer,
    RoomSerializer,
)


@extend_schema(tags=["activities"])
class ActivityViewSet(viewsets.ModelViewSet):
    """Activities, their filters and their enrolments."""

    serializer_class = ActivitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["starts_at", "name", "capacity"]

    def get_queryset(self):
        queryset = (
            Activity.objects.select_related("instructor", "main_room")
            .prefetch_related("secondary_rooms")
            .annotate(enrollment_count=Count("enrollments"))
        )

        category = self.request.query_params.get("category")
        instructor = self.request.query_params.get("instructor")
        if category:
            queryset = queryset.filter(category=category)
        if instructor and instructor.isdigit():
            queryset = queryset.filter(instructor_id=instructor)

        return queryset.order_by("starts_at")

    @extend_schema(
        parameters=[
            OpenApiParameter("category", str, description="Filter by category."),
            OpenApiParameter("instructor", int, description="Filter by instructor id."),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=EnrollmentCreateSerializer,
        responses={200: EnrollmentSerializer, 201: EnrollmentSerializer},
        description=(
            "GET lists the members enrolled in the activity. POST enrols one: "
            "201 when the place is new, 200 when the member already had one, "
            "and 400 when the activity is full."
        ),
    )
    @action(detail=True, methods=["get", "post"], url_path="enrollments")
    def enrollments(self, request, pk=None):
        activity = self.get_object()

        if request.method == "POST":
            body = EnrollmentCreateSerializer(data=request.data)
            body.is_valid(raise_exception=True)

            try:
                enrollment, created = services.enroll(
                    activity, body.validated_data["member"]
                )
            except services.ActivityFull as error:
                raise ValidationError({"detail": str(error)})

            return Response(
                EnrollmentSerializer(enrollment).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        enrollments = activity.enrollments.select_related("member")
        page = self.paginate_queryset(enrollments)
        serializer = EnrollmentSerializer(page or enrollments, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        responses={204: None},
        description="Remove a member's place in the activity.",
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"enrollments/(?P<member_id>[0-9]+)",
    )
    def remove_enrollment(self, request, pk=None, member_id=None):
        activity = self.get_object()

        if not services.unenroll(activity, member_id):
            raise NotFound("That member is not enrolled in this activity.")

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["members"])
class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "email"]
    ordering_fields = ["full_name", "email"]

    def get_queryset(self):
        queryset = super().get_queryset()
        activity = self.request.query_params.get("activity")
        if activity and activity.isdigit():
            queryset = queryset.filter(enrollments__activity_id=activity).distinct()
        return queryset


@extend_schema(tags=["instructors"])
class InstructorViewSet(viewsets.ModelViewSet):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "specialty"]
    ordering_fields = ["full_name"]


@extend_schema(tags=["rooms"])
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("manager")
    serializer_class = RoomSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "location"]
    ordering_fields = ["name", "capacity"]
