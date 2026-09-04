"""Model forms used by the create and update views."""

from django import forms

from .models import Activity, Enrollment, Instructor, Member, Room


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "name",
            "category",
            "starts_at",
            "duration",
            "description",
            "capacity",
            "instructor",
            "main_room",
            "secondary_rooms",
        ]
        widgets = {
            "starts_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "secondary_rooms": forms.SelectMultiple(attrs={"size": 4}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["member"]


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["full_name", "email", "phone"]


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ["full_name", "specialty"]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name", "capacity", "location", "manager"]
