"""Domain model for the cultural centre.

Four entities and one explicit join table: members enrol in activities through
`Enrollment`, which is a `through` model so the enrolment date is recorded and
the same member cannot be enrolled twice in the same activity.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Member(models.Model):
    """Someone registered at the centre who can enrol in activities."""

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("member-detail", kwargs={"pk": self.pk})


class Instructor(models.Model):
    """A member of staff who runs activities and may manage a room."""

    full_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("instructor-detail", kwargs={"pk": self.pk})


class Room(models.Model):
    """A physical space where activities take place."""

    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=100)
    manager = models.ForeignKey(
        Instructor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_rooms",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("room-detail", kwargs={"pk": self.pk})


class Activity(models.Model):
    """A scheduled activity with a capacity, a room and an instructor."""

    class Category(models.TextChoices):
        DANCE = "dance", "Dance"
        MUSIC = "music", "Music"
        THEATRE = "theatre", "Theatre"
        FOOTBALL = "football", "Football"
        BASKETBALL = "basketball", "Basketball"
        SWIMMING = "swimming", "Swimming"

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    starts_at = models.DateTimeField()
    duration = models.DurationField(help_text="Format: HH:MM:SS, e.g. 01:30:00.")
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(help_text="Total number of places offered.")

    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    main_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="main_activities",
    )
    secondary_rooms = models.ManyToManyField(
        Room,
        blank=True,
        related_name="secondary_activities",
    )
    members = models.ManyToManyField(
        Member,
        through="Enrollment",
        related_name="activities",
    )

    class Meta:
        ordering = ["starts_at"]
        verbose_name_plural = "activities"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("activity-detail", kwargs={"pk": self.pk})

    @property
    def places_taken(self):
        return self.enrollments.count()

    @property
    def places_left(self):
        return max(self.capacity - self.places_taken, 0)

    @property
    def is_full(self):
        return self.places_taken >= self.capacity

    def clean(self):
        """An activity cannot offer more places than its main room holds."""
        super().clean()
        if self.main_room and self.capacity > self.main_room.capacity:
            raise ValidationError(
                {
                    "capacity": (
                        f"{self.main_room} holds {self.main_room.capacity} people, "
                        f"so this activity cannot offer {self.capacity} places."
                    )
                }
            )


class Enrollment(models.Model):
    """A member's place in an activity."""

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="enrollments"
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="enrollments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "activity"],
                name="unique_member_per_activity",
            )
        ]

    def __str__(self):
        return f"{self.member} in {self.activity}"
