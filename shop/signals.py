"""
Signal wiring for outbound status sync (Django -> Slack).

We snapshot ``status`` when an instance loads (post_init) and, on save
(post_save), fire the Slack sync only when the status actually changed. This
catches status edits from anywhere — admin list/inline edits, the change form,
actions, or code — not just one code path.
"""

import logging

from django.db.models.signals import post_init, post_save

from shop.models import (
    BeeRemovalRequest,
    CallbackRequest,
    NukeRequest,
    Order,
    PollinationRequest,
)
from shop.services import slack_sync

logger = logging.getLogger(__name__)

TRACKED_MODELS = (Order, NukeRequest, PollinationRequest, BeeRemovalRequest, CallbackRequest)


def _remember_status(sender, instance, **kwargs):
    instance._original_status = instance.status


def _sync_on_status_change(sender, instance, created, **kwargs):
    source = getattr(instance, '_status_change_source', None)
    if created:
        instance._original_status = instance.status
        return
    old = getattr(instance, '_original_status', None)
    new = instance.status
    if old == new:
        return
    instance._original_status = new
    try:
        slack_sync.sync_status_to_slack(instance, source=source)
    except Exception:
        logger.exception("Failed to sync status change to Slack")


def connect():
    for model in TRACKED_MODELS:
        post_init.connect(_remember_status, sender=model, dispatch_uid='slack_remember_status')
        post_save.connect(_sync_on_status_change, sender=model, dispatch_uid='slack_sync_status')
