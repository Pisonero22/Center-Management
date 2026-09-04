"""Serializers for the REST API."""

import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ..models import Activity, Enrollment, Instructor, Member, Room


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ["id", "full_name", "specialty"]


class RoomSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(
        source="manager.full_name", read_only=True, default=None
    )

    class Meta:
        model = Room
        fields = ["id", "name", "capacity", "location", "manager", "manager_name"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["id", "full_name", "email", "phone"]


class ActivitySerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True, default=None
    )
    main_room_name = serializers.CharField(
        source="main_room.name", read_only=True, default=None
    )
    places_left = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "category",
            "starts_at",
            "duration",
            "description",
            "capacity",
            "places_left",
            "is_full",
            "instructor",
            "instructor_name",
            "main_room",
            "main_room_name",
            "secondary_rooms",
        ]

    def validate(self, attrs):
        """Reuse the model's own rule instead of restating it here."""
        if self.instance is None:
            candidate = Activity(
                **{key: value for key, value in attrs.items() if key != "secondary_rooms"}
            )
        else:
            candidate = copy.copy(self.instance)
            for field, value in attrs.items():
                if field != "secondary_rooms":
                    setattr(candidate, field, value)

        try:
            candidate.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(serializers.as_serializer_error(error))

        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    """An enrolment as it is read back."""

    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "member", "member_name", "activity", "created_at"]
        read_only_fields = ["activity", "created_at"]


class EnrollmentCreateSerializer(serializers.Serializer):
    """The body of a request that enrols someone: just the member."""

    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
