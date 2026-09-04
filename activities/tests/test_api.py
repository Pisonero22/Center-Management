"""Tests for the REST API: permissions, filters and the enrolment rules."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from activities.models import Activity, Enrollment

from .factories import make_activity, make_instructor, make_member, make_room


class PublicReadTests(APITestCase):
    def setUp(self):
        self.activity = make_activity(name="Contemporary dance")

    def test_the_activity_list_is_public_and_paginated(self):
        response = self.client.get(reverse("api:activity-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Contemporary dance")

    def test_an_activity_reports_its_remaining_places(self):
        Enrollment.objects.create(activity=self.activity, member=make_member())

        response = self.client.get(
            reverse("api:activity-detail", args=[self.activity.pk])
        )

        self.assertEqual(response.data["capacity"], 10)
        self.assertEqual(response.data["places_left"], 9)
        self.assertFalse(response.data["is_full"])

    def test_writing_without_an_account_is_refused(self):
        response = self.client.post(reverse("api:activity-list"), {"name": "New"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Activity.objects.count(), 1)

    def test_the_schema_is_served(self):
        self.assertEqual(self.client.get(reverse("api:schema")).status_code, 200)


class FilterTests(APITestCase):
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

    def names(self, response):
        return [row["name"] for row in response.data["results"]]

    def test_filtering_by_category(self):
        response = self.client.get(reverse("api:activity-list"), {"category": "music"})

        self.assertEqual(self.names(response), ["Guitar ensemble"])

    def test_filtering_by_instructor(self):
        response = self.client.get(
            reverse("api:activity-list"), {"instructor": self.instructor.pk}
        )

        self.assertEqual(self.names(response), ["Contemporary dance"])

    def test_searching_by_name(self):
        response = self.client.get(reverse("api:activity-list"), {"search": "guitar"})

        self.assertEqual(self.names(response), ["Guitar ensemble"])

    def test_an_unparsable_filter_is_ignored_rather_than_crashing(self):
        response = self.client.get(reverse("api:activity-list"), {"instructor": "abc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class WriteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("staff", password="staff-pass-123")
        self.client.force_login(self.user)

    def test_creating_an_activity(self):
        response = self.client.post(
            reverse("api:activity-list"),
            {
                "name": "Theatre workshop",
                "category": Activity.Category.THEATRE,
                "starts_at": "2027-01-15T18:00:00Z",
                "duration": "03:00:00",
                "capacity": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Activity.objects.filter(name="Theatre workshop").exists())

    def test_an_activity_larger_than_its_room_is_rejected(self):
        room = make_room(capacity=10)

        response = self.client.post(
            reverse("api:activity-list"),
            {
                "name": "Too big",
                "category": Activity.Category.DANCE,
                "starts_at": "2027-01-15T18:00:00Z",
                "duration": "01:00:00",
                "capacity": 40,
                "main_room": room.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.data)


class EnrollmentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("staff", password="staff-pass-123")
        self.client.force_login(self.user)
        self.activity = make_activity(capacity=1)
        self.member = make_member(full_name="Clara Ferreira")
        self.other = make_member(full_name="Diego Ramos")
        self.url = reverse("api:activity-enrollments", args=[self.activity.pk])

    def test_enrolling_a_member(self):
        response = self.client.post(self.url, {"member": self.member.pk})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["member_name"], "Clara Ferreira")
        self.assertEqual(self.activity.enrollments.count(), 1)

    def test_enrolling_twice_returns_the_existing_place(self):
        self.client.post(self.url, {"member": self.member.pk})

        response = self.client.post(self.url, {"member": self.member.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.activity.enrollments.count(), 1)

    def test_a_full_activity_is_a_bad_request(self):
        self.client.post(self.url, {"member": self.member.pk})

        response = self.client.post(self.url, {"member": self.other.pk})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is full", str(response.data["detail"]))
        self.assertEqual(self.activity.enrollments.count(), 1)

    def test_removing_a_place(self):
        self.client.post(self.url, {"member": self.member.pk})
        url = reverse(
            "api:activity-remove-enrollment", args=[self.activity.pk, self.member.pk]
        )

        self.assertEqual(
            self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(
            self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND
        )
