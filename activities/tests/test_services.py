"""Tests for the enrolment rules, at the level both entry points share."""

from django.test import TestCase

from activities import services

from .factories import make_activity, make_member


class EnrollTests(TestCase):
    def setUp(self):
        self.activity = make_activity(capacity=1)
        self.member = make_member(full_name="Clara Ferreira")

    def test_enrolling_reports_a_new_place(self):
        enrollment, created = services.enroll(self.activity, self.member)

        self.assertTrue(created)
        self.assertEqual(enrollment.activity, self.activity)

    def test_enrolling_again_returns_the_existing_place(self):
        first, _ = services.enroll(self.activity, self.member)
        second, created = services.enroll(self.activity, self.member)

        self.assertFalse(created)
        self.assertEqual(first, second)
        self.assertEqual(self.activity.enrollments.count(), 1)

    def test_a_full_activity_raises(self):
        services.enroll(self.activity, self.member)

        with self.assertRaises(services.ActivityFull):
            services.enroll(self.activity, make_member(full_name="Diego Ramos"))

    def test_the_message_agrees_with_the_number_of_places(self):
        services.enroll(self.activity, self.member)

        with self.assertRaisesMessage(services.ActivityFull, "(1 place)"):
            services.enroll(self.activity, make_member(full_name="Diego Ramos"))


class UnenrollTests(TestCase):
    def test_removing_a_place_reports_whether_there_was_one(self):
        activity = make_activity()
        member = make_member()
        services.enroll(activity, member)

        self.assertTrue(services.unenroll(activity, member.pk))
        self.assertFalse(services.unenroll(activity, member.pk))
