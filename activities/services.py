"""Business rules that more than one entry point needs.

The HTML views and the REST API both enrol members, and the capacity rule must
behave identically in both. Keeping it here is what stops the two from drifting
apart.
"""

from django.db import transaction

from .models import Activity, Enrollment


class ActivityFull(Exception):
    """Raised when an activity has no places left."""


@transaction.atomic
def enroll(activity, member):
    """Enrol `member` in `activity`.

    Returns `(enrollment, created)`; `created` is False when the member already
    had a place. Raises `ActivityFull` when there is none left.

    The count and the insert share a transaction and a row lock, so two people
    claiming the last place at the same time cannot both get it. The lock is a
    no-op on SQLite and does the work on PostgreSQL.
    """
    locked = Activity.objects.select_for_update().get(pk=activity.pk)

    existing = Enrollment.objects.filter(activity=locked, member=member).first()
    if existing is not None:
        return existing, False

    if locked.is_full:
        places = "place" if locked.capacity == 1 else "places"
        raise ActivityFull(f"{locked.name} is full ({locked.capacity} {places}).")

    return Enrollment.objects.create(activity=locked, member=member), True


def unenroll(activity, member_id):
    """Remove a member's place. Returns True when there was one to remove."""
    deleted, _ = Enrollment.objects.filter(
        activity=activity, member_id=member_id
    ).delete()
    return bool(deleted)
