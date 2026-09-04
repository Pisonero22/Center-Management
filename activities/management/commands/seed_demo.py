"""Populate the database with a small, realistic demo dataset.

    python manage.py seed_demo

Useful to try the app out (or to take screenshots) without typing data by
hand. The command is idempotent: running it twice does not duplicate rows.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from activities.models import Activity, Enrollment, Instructor, Member, Room

INSTRUCTORS = [
    ("Aoife Byrne", "Contemporary dance"),
    ("Marcus Hall", "Classical guitar"),
    ("Nora Kavanagh", "Stage acting"),
]

ROOMS = [
    ("Main Hall", 120, "Ground floor"),
    ("Studio A", 30, "First floor"),
    ("Rehearsal Room", 18, "Basement"),
]

MEMBERS = [
    ("Clara Ferreira", "clara.ferreira@example.com", "+353 1 555 0101"),
    ("Diego Ramos", "diego.ramos@example.com", "+353 1 555 0102"),
    ("Hannah Doyle", "hannah.doyle@example.com", "+353 1 555 0103"),
    ("Ivan Petrov", "ivan.petrov@example.com", "+353 1 555 0104"),
]

ACTIVITIES = [
    # name, category, days from now, hours, duration, capacity, room, instructor
    ("Contemporary dance", Activity.Category.DANCE, 2, 18, 90, 20, "Studio A", "Aoife Byrne"),
    ("Guitar ensemble", Activity.Category.MUSIC, 4, 19, 120, 12, "Rehearsal Room", "Marcus Hall"),
    ("Theatre workshop", Activity.Category.THEATRE, 7, 17, 180, 25, "Main Hall", "Nora Kavanagh"),
]


class Command(BaseCommand):
    help = "Create a small demo dataset (instructors, rooms, members, activities)."

    def handle(self, *args, **options):
        instructors = {
            name: Instructor.objects.get_or_create(
                full_name=name, defaults={"specialty": specialty}
            )[0]
            for name, specialty in INSTRUCTORS
        }

        rooms = {}
        for index, (name, capacity, location) in enumerate(ROOMS):
            manager = list(instructors.values())[index % len(instructors)]
            rooms[name] = Room.objects.get_or_create(
                name=name,
                defaults={
                    "capacity": capacity,
                    "location": location,
                    "manager": manager,
                },
            )[0]

        members = [
            Member.objects.get_or_create(
                email=email, defaults={"full_name": full_name, "phone": phone}
            )[0]
            for full_name, email, phone in MEMBERS
        ]

        now = timezone.now()
        for name, category, days, hour, minutes, capacity, room, instructor in ACTIVITIES:
            starts_at = (now + timedelta(days=days)).replace(
                hour=hour, minute=0, second=0, microsecond=0
            )
            activity, _ = Activity.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "starts_at": starts_at,
                    "duration": timedelta(minutes=minutes),
                    "description": f"{name} run by {instructor}.",
                    "capacity": capacity,
                    "instructor": instructors[instructor],
                    "main_room": rooms[room],
                },
            )
            activity.secondary_rooms.add(rooms["Main Hall"])
            for member in members[:2]:
                Enrollment.objects.get_or_create(activity=activity, member=member)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {Instructor.objects.count()} instructors, "
                f"{Room.objects.count()} rooms, {Member.objects.count()} members, "
                f"{Activity.objects.count()} activities."
            )
        )
