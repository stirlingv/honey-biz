"""Tests for the printable Google-review QR card page (/review)."""

from django.test import TestCase, override_settings
from django.urls import reverse


class ReviewCardTests(TestCase):
    @override_settings(GOOGLE_REVIEW_URL='https://g.page/r/EXAMPLE/review')
    def test_page_shows_review_link_and_qr(self):
        resp = self.client.get(reverse('review_card'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'https://g.page/r/EXAMPLE/review')
        self.assertContains(resp, 'images/review-qr.png')

    def test_page_is_not_indexed(self):
        # The card is a utility page, not something we want ranking in search.
        resp = self.client.get(reverse('review_card'))
        self.assertContains(resp, 'noindex')
