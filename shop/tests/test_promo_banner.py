"""Tests for the date-gated seasonal promo banner."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone


class PromoBannerTests(TestCase):
    """The promo only appears while today is inside the configured window."""

    def setUp(self):
        self.today = timezone.localdate()

    def _window(self, start_offset, end_offset):
        return override_settings(
            PROMO_BANNER_START=self.today + timedelta(days=start_offset),
            PROMO_BANNER_END=self.today + timedelta(days=end_offset),
        )

    def test_bar_and_graphic_show_during_window(self):
        with self._window(-1, 1):
            response = self.client.get(reverse('home'))
        self.assertContains(response, 'promo-bar')
        self.assertContains(response, '4th-of-july')

    def test_bar_shows_site_wide_during_window(self):
        with self._window(-1, 1):
            response = self.client.get(reverse('products'))
        self.assertContains(response, 'promo-bar')

    def test_hidden_after_window(self):
        with self._window(-10, -1):
            response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')
        self.assertNotContains(response, '4th-of-july')

    def test_hidden_before_window(self):
        with self._window(1, 10):
            response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')

    def test_inclusive_on_final_day(self):
        with self._window(-5, 0):
            response = self.client.get(reverse('home'))
        self.assertContains(response, 'promo-bar')

    @override_settings(PROMO_BANNER_START=None, PROMO_BANNER_END=None)
    def test_disabled_when_no_end_date(self):
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')
