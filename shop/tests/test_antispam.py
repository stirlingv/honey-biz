"""Anti-spam tests: honeypot + submission-timing trap on public forms.

The traps must stop scripted spam (the gibberish callback/order submissions the
business was receiving) while never blocking a genuine visitor.
"""

import time
from unittest.mock import patch

from django.core import signing
from django.test import TestCase
from django.urls import reverse

from shop.forms import _TIMESTAMP_SALT
from shop.models import CallbackRequest


def _fresh_token(age_seconds=0):
    """A validly-signed render timestamp `age_seconds` in the past."""
    return signing.dumps(time.time() - age_seconds, salt=_TIMESTAMP_SALT)


class CallbackSpamTests(TestCase):
    url = "callback_request"

    def _payload(self, **o):
        # A well-formed-looking human submission, submitted slow enough to pass
        # the timing check (token rendered a minute ago).
        data = dict(
            name="Sam Bee", phone="850-555-0101", email="sam@example.com",
            interest="general", best_time="Mornings", message="Hi there",
            loaded_at=_fresh_token(age_seconds=60),
        )
        data.update(o)
        return data

    @patch("shop.views.notify_new_callback_request")
    def test_honeypot_filled_is_rejected(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(website="http://spam.example"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 0)
        notify.assert_not_called()

    @patch("shop.views.notify_new_callback_request")
    def test_instant_submission_is_rejected(self, notify):
        # Bot posts the form the instant it renders (token age ~0).
        resp = self.client.post(reverse(self.url), self._payload(loaded_at=_fresh_token(0)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 0)
        notify.assert_not_called()

    @patch("shop.views.notify_new_callback_request")
    def test_genuine_submission_still_succeeds(self, notify):
        resp = self.client.post(reverse(self.url), self._payload())
        self.assertRedirects(resp, reverse("callback_success"))
        callback = CallbackRequest.objects.get()
        self.assertEqual(callback.name, "Sam Bee")
        notify.assert_called_once_with(callback)

    @patch("shop.views.notify_new_callback_request")
    def test_missing_token_fails_open(self, notify):
        # A submission without any timing token (e.g. an integration that posts
        # directly) is still accepted — the honeypot is the backstop, not timing.
        resp = self.client.post(reverse(self.url), self._payload(loaded_at=""))
        self.assertRedirects(resp, reverse("callback_success"))
        notify.assert_called_once()

    @patch("shop.views.notify_new_callback_request")
    def test_tampered_token_fails_open(self, notify):
        resp = self.client.post(reverse(self.url), self._payload(loaded_at="not-a-valid-token"))
        self.assertRedirects(resp, reverse("callback_success"))
        notify.assert_called_once()

    def test_get_renders_hidden_honeypot_and_timestamp(self):
        resp = self.client.get(reverse(self.url))
        self.assertContains(resp, 'name="website"')
        self.assertContains(resp, 'name="loaded_at"')

