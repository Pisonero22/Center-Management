"""Tests for the domain rules that live in the models."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from activities.models import Enrollment

from .factories import make_activity, make_member, make_room


class EnrollmentConstraintTests(TestCase):
    def setUp(self):
        self.activity = make_activity()
        self.member = make_member()

    def test_a_member_can_only_be_enrolled_once_in_an_activity(self):
        Enrollment.objects.create(activity=self.activity, member=self.member)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(activity=self.activity, member=self.member)

    def test_the_same_member_can_join_two_activities(self):
        other = make_activity(name="Guitar ensemble")

        Enrollment.objects.create(activity=self.activity, member=self.member)
        Enrollment.objects.create(activity=other, member=self.member)

        self.assertEqual(self.member.enrollments.count(), 2)


class ActivityCapacityTests(TestCase):
    def test_places_left_counts_the_enrolments(self):
        activity = make_activity(capacity=3)
        Enrollment.objects.create(activity=activity, member=make_member())

        self.assertEqual(activity.places_taken, 1)
        self.assertEqual(activity.places_left, 2)
        self.assertFalse(activity.is_full)

    def test_an_activity_is_full_once_every_place_is_taken(self):
        activity = make_activity(capacity=1)
        Enrollment.objects.create(activity=activity, member=make_member())

        self.assertTrue(activity.is_full)
        self.assertEqual(activity.places_left, 0)

    def test_places_left_never_goes_negative(self):
        activity = make_activity(capacity=1)
        Enrollment.objects.create(activity=activity, member=make_member(full_name="A B"))
        Enrollment.objects.create(activity=activity, member=make_member(full_name="C D"))

        self.assertEqual(activity.places_left, 0)

    def test_places_taken_reuses_an_annotation_when_the_view_provides_one(self):
        activity = make_activity(capacity=5)
        Enrollment.objects.create(activity=activity, member=make_member())
        activity.enrollment_count = 4

        self.assertEqual(activity.places_taken, 4)


class ActivityValidationTests(TestCase):
    def test_an_activity_cannot_offer_more_places_than_its_main_room_holds(self):
        room = make_room(capacity=10)
        activity = make_activity(capacity=25, main_room=room)

        with self.assertRaises(ValidationError) as error:
            activity.full_clean()

        self.assertIn("capacity", error.exception.message_dict)

    def test_an_activity_that_fits_its_room_is_valid(self):
        room = make_room(capacity=30)
        activity = make_activity(capacity=25, main_room=room)

        activity.full_clean()  # must not raise


class StringRepresentationTests(TestCase):
    def test_models_are_readable_in_the_admin(self):
        activity = make_activity(name="Theatre workshop")
        member = make_member(full_name="Hannah Doyle")
        enrollment = Enrollment.objects.create(activity=activity, member=member)

        self.assertEqual(str(activity), "Theatre workshop")
        self.assertEqual(str(member), "Hannah Doyle")
        self.assertEqual(str(enrollment), "Hannah Doyle in Theatre workshop")
