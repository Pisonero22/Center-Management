"""Tests for the views: what a visitor may do, and the enrolment rules."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from activities.models import Activity, Enrollment

from .factories import make_activity, make_instructor, make_member


class PublicAccessTests(TestCase):
    def setUp(self):
        self.activity = make_activity()

    def test_the_catalogue_is_public(self):
        for url in [
            reverse("home"),
            reverse("activity-list"),
            reverse("activity-detail", args=[self.activity.pk]),
            reverse("member-list"),
            reverse("room-list"),
            reverse("instructor-list"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_writing_requires_a_signed_in_user(self):
        for url in [
            reverse("activity-create"),
            reverse("activity-update", args=[self.activity.pk]),
            reverse("activity-delete", args=[self.activity.pk]),
            reverse("member-create"),
            reverse("activity-enroll", args=[self.activity.pk]),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")


class EnrollmentFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("staff", password="staff-pass-123")
        self.client.force_login(self.user)
        self.activity = make_activity(capacity=1)
        self.member = make_member(full_name="Clara Ferreira")
        self.other_member = make_member(full_name="Diego Ramos")
        self.url = reverse("activity-enroll", args=[self.activity.pk])

    def test_enrolling_a_member_creates_the_enrolment(self):
        response = self.client.post(self.url, {"member": self.member.pk}, follow=True)

        self.assertTrue(
            Enrollment.objects.filter(
                activity=self.activity, member=self.member
            ).exists()
        )
        self.assertContains(response, "is now enrolled")

    def test_enrolling_the_same_member_twice_does_not_duplicate(self):
        activity = make_activity(name="Guitar ensemble", capacity=5)
        url = reverse("activity-enroll", args=[activity.pk])

        self.client.post(url, {"member": self.member.pk})
        response = self.client.post(url, {"member": self.member.pk}, follow=True)

        self.assertEqual(activity.enrollments.count(), 1)
        self.assertContains(response, "was already enrolled")

    def test_a_full_activity_refuses_new_members(self):
        self.client.post(self.url, {"member": self.member.pk})

        response = self.client.post(
            self.url, {"member": self.other_member.pk}, follow=True
        )

        self.assertEqual(self.activity.enrollments.count(), 1)
        self.assertContains(response, "is full")

    def test_removing_an_enrolment_needs_a_post(self):
        Enrollment.objects.create(activity=self.activity, member=self.member)
        url = reverse("enrollment-remove", args=[self.activity.pk, self.member.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.activity.enrollments.count(), 1)

        self.client.post(url)
        self.assertEqual(self.activity.enrollments.count(), 0)


class FilterTests(TestCase):
    def setUp(self):
        self.instructor = make_instructor()
        self.dance = make_activity(
            name="Contemporary dance",
            category=Activity.Category.DANCE,
            instructor=self.instructor,
        )
        self.music = make_activity(
            name="Guitar ensemble", category=Activity.Category.MUSIC
        )

    def test_activities_can_be_filtered_by_category(self):
        response = self.client.get(reverse("activity-list"), {"category": "music"})

        self.assertQuerySetEqual(response.context["activities"], [self.music])

    def test_activities_can_be_filtered_by_instructor(self):
        response = self.client.get(
            reverse("activity-list"), {"instructor": self.instructor.pk}
        )

        self.assertQuerySetEqual(response.context["activities"], [self.dance])

    def test_members_can_be_filtered_by_the_activity_they_attend(self):
        member = make_member()
        Enrollment.objects.create(activity=self.dance, member=member)
        make_member(full_name="Someone Else")

        response = self.client.get(reverse("member-list"), {"activity": self.dance.pk})

        self.assertQuerySetEqual(response.context["members"], [member])


class ListViewEfficiencyTests(TestCase):
    def setUp(self):
        instructor = make_instructor()
        for index in range(12):
            activity = make_activity(
                name=f"Activity {index:02d}", instructor=instructor, capacity=5
            )
            Enrollment.objects.create(
                activity=activity, member=make_member(full_name=f"Member {index:02d}")
            )

    def test_the_activity_list_is_paginated(self):
        first_page = self.client.get(reverse("activity-list"))
        second_page = self.client.get(reverse("activity-list"), {"page": 2})

        self.assertEqual(len(first_page.context["activities"]), 10)
        self.assertEqual(len(second_page.context["activities"]), 2)

    def test_the_activity_list_does_not_run_one_query_per_row(self):
        # Page of activities, pagination count, and the instructors used by the
        # filter: three queries no matter how many rows are shown.
        with self.assertNumQueries(3):
            self.client.get(reverse("activity-list"))
