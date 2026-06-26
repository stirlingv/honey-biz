"""Integration tests for the service-request workflows.

Each form should: render on GET, create a record + fire a notification +
redirect on a valid POST, and create nothing on an invalid POST.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shop.models import BeeRemovalRequest, CallbackRequest, NukeRequest, PollinationRequest

FUTURE = (date.today() + timedelta(days=30)).isoformat()


class NucRequestTests(TestCase):
    url = "nuke_request"

    def _payload(self, **o):
        data = dict(
            first_name="Bea", last_name="Keeper", email="Bea@Example.com", phone="850-555-0101",
            address="2 Hive Rd", city="Quincy", state="FL", zip_code="32351",
            quantity=2, experience_level="beginner", notes="",
        )
        data.update(o)
        return data

    def test_get_renders(self):
        self.assertEqual(self.client.get(reverse(self.url)).status_code, 200)

    @patch("shop.views.notify_new_nuc_request")
    def test_valid_post_creates_and_notifies(self, notify):
        resp = self.client.post(reverse(self.url), self._payload())
        self.assertRedirects(resp, reverse("nuke_success"))
        req = NukeRequest.objects.get()
        self.assertEqual(req.email, "bea@example.com")
        self.assertEqual(req.phone, "(850) 555-0101")
        notify.assert_called_once_with(req)

    @patch("shop.views.notify_new_nuc_request")
    def test_invalid_post_creates_nothing(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(phone="bad"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(NukeRequest.objects.count(), 0)
        notify.assert_not_called()


class PollinationRequestTests(TestCase):
    url = "pollination_services"

    def _payload(self, **o):
        data = dict(
            first_name="Far", last_name="Mer", email="far@example.com", phone="8505550202",
            property_address="100 Grove Ln", city="Havana", state="FL", zip_code="32333",
            crop_type="blueberries", acreage="5.0", preferred_start_date=FUTURE,
            duration_weeks=4, notes="",
        )
        data.update(o)
        return data

    def test_get_renders(self):
        self.assertEqual(self.client.get(reverse(self.url)).status_code, 200)

    @patch("shop.views.notify_new_pollination_request")
    def test_valid_post_creates_and_notifies(self, notify):
        resp = self.client.post(reverse(self.url), self._payload())
        self.assertRedirects(resp, reverse("pollination_success"))
        notify.assert_called_once_with(PollinationRequest.objects.get())

    @patch("shop.views.notify_new_pollination_request")
    def test_invalid_post_creates_nothing(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(acreage=""))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(PollinationRequest.objects.count(), 0)
        notify.assert_not_called()


class BeeRemovalRequestTests(TestCase):
    url = "bee_removal"

    def _payload(self, **o):
        data = dict(
            first_name="Home", last_name="Owner", email="home@example.com", phone="8505550303",
            property_address="9 Oak St", city="Tallahassee", state="FL", zip_code="32301",
            property_type="residential", bee_location="wall", how_long_present="2 weeks",
            urgency="medium", notes="",
        )
        data.update(o)
        return data

    def test_get_renders(self):
        self.assertEqual(self.client.get(reverse(self.url)).status_code, 200)

    @patch("shop.views.notify_new_bee_removal")
    def test_valid_post_creates_and_notifies(self, notify):
        resp = self.client.post(reverse(self.url), self._payload())
        self.assertRedirects(resp, reverse("bee_removal_success"))
        notify.assert_called_once_with(BeeRemovalRequest.objects.get())

    @patch("shop.views.notify_new_bee_removal")
    def test_invalid_post_creates_nothing(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(how_long_present=""))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(BeeRemovalRequest.objects.count(), 0)
        notify.assert_not_called()


class CallbackRequestTests(TestCase):
    url = "callback_request"

    def _payload(self, **o):
        data = dict(name="Cal Ler", phone="850-555-0404", email="", interest="honey",
                    best_time="Mornings", message="")
        data.update(o)
        return data

    def test_get_renders(self):
        self.assertEqual(self.client.get(reverse(self.url)).status_code, 200)

    @patch("shop.views.notify_new_callback_request")
    def test_valid_post_creates_and_notifies(self, notify):
        resp = self.client.post(reverse(self.url), self._payload())
        self.assertRedirects(resp, reverse("callback_success"))
        notify.assert_called_once_with(CallbackRequest.objects.get())

    @patch("shop.views.notify_new_callback_request")
    def test_invalid_post_creates_nothing(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(phone=""))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 0)
        notify.assert_not_called()

    def test_get_prefills_valid_interest_from_querystring(self):
        resp = self.client.get(reverse(self.url), {"interest": "honey"})
        self.assertEqual(resp.context["form"]["interest"].value(), "honey")

    def test_get_ignores_invalid_interest(self):
        # An unrecognized interest is ignored, leaving the model's default ('general').
        resp = self.client.get(reverse(self.url), {"interest": "not-a-real-interest"})
        self.assertEqual(resp.context["form"]["interest"].value(), "general")
