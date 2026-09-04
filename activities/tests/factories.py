"""Small helpers to build objects in tests without repeating boilerplate."""

from datetime import timedelta

from django.utils import timezone

from activities.models import Activity, Instructor, Member, Room


def make_instructor(**kwargs):
    kwargs.setdefault("full_name", "Aoife Byrne")
    kwargs.setdefault("specialty", "Contemporary dance")
    return Instructor.objects.create(**kwargs)


def make_room(**kwargs):
    kwargs.setdefault("name", "Studio A")
    kwargs.setdefault("capacity", 30)
    kwargs.setdefault("location", "First floor")
    return Room.objects.create(**kwargs)


def make_member(**kwargs):
    kwargs.setdefault("full_name", "Clara Ferreira")
    kwargs.setdefault("email", f"{kwargs['full_name'].lower().replace(' ', '.')}@example.com")
    return Member.objects.create(**kwargs)


def make_activity(**kwargs):
    kwargs.setdefault("name", "Contemporary dance")
    kwargs.setdefault("category", Activity.Category.DANCE)
    kwargs.setdefault("starts_at", timezone.now() + timedelta(days=1))
    kwargs.setdefault("duration", timedelta(hours=1, minutes=30))
    kwargs.setdefault("capacity", 10)
    return Activity.objects.create(**kwargs)
