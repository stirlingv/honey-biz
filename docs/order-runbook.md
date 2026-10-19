# Order runbook

How an order moves through the system, end to end. This is the canonical
description of the ordering process — **keep it current**: when you change a
view, form, notification, or the fulfillment flow, update this file in the same
change so future work (and future Claude sessions) starts from the truth.

Related docs: `docs/growth.md` (SEO/feed + ordering-UX features),
`docs/promotions.md` (seasonal discount mechanics).

## The big picture

There is **no online payment and no cart**. An "order" is a single form
submission that notifies the family, who then invoice by hand through
QuickBooks. Everything downstream is coordinated by a human over phone/text; the
software's job is to capture the request, alert the family, and track status.

```
Customer submits form
        │
        ▼
Order saved (status=pending)  ──►  Slack alert to family  (+ admin email)
        │                                   │
        ▼                                   ▼
Confirmation page shown            Family sends QuickBooks invoice by hand
                                            │
                                            ▼
                                   Family reacts on the Slack message
                                   to advance status (see below)
```

## Order channels

Five separate submission flows, each a function-based view in `shop/views.py`
with a `ModelForm` in `shop/forms.py` and a `notify_*` call in
`shop/services/notifications.py`:

| Flow | URL name | Model | Notification |
|---|---|---|---|
| Honey order | `order_honey` | `Order` | `notify_new_order` |
| Bee nucs | `nuke_request` | `NukeRequest` | `notify_new_nuc_request` |
| Pollination | `pollination_services` | `PollinationRequest` | `notify_new_pollination_request` |
| Bee removal | `bee_removal` | `BeeRemovalRequest` | `notify_new_bee_removal` |
| Callback | `callback_request` | `CallbackRequest` | `notify_new_callback_request` |

The rest of this doc focuses on the **honey order** flow; the others follow the
same shape (submit → save → Slack + email → success page → reaction-driven
status).

## Honey order lifecycle

### 1. Submission (`order_honey` in `shop/views.py`)
- Single step: the submitted `OrderForm` **is** the order. On valid POST it
  saves the `Order`, calls `notify_new_order(order)`, stashes the id in the
  session, and redirects to the confirmation page. No separate review step.
- Arriving from a product ("Order Now") deep-links `?product=<pk>` (and
  optionally `?quantity=`), which pre-fills and shows an order summary; the
  product is submitted as a hidden field. Otherwise the customer picks from a
  dropdown of in-stock products.
- Quantity is capped at `MAX_SELF_SERVE_QUANTITY` (24). Larger orders are
  rejected with a pointer to the callback flow for bulk pricing.

### 2. Fulfillment: pickup vs. delivery (`Order.fulfillment`)
- The form asks **"How would you like to get it?"** — `delivery` (default) or
  `pickup`.
- **Delivery:** address/city/state/ZIP are required (enforced in
  `OrderForm.clean()`, since the fields are `required = False` at the widget
  level and conditionally validated).
- **Pickup:** the address section is hidden (JS) and not required; the fields
  save blank. `Order.is_pickup` / `Order.full_address` reflect this.
- **Pickup location is coordinated by hand.** By deliberate choice there is no
  published pickup address on the site — the family texts/calls the customer to
  set a spot and time. The confirmation page and Slack alert say so. (If this
  ever changes, update the form copy, the success page, `notify_new_order`, and
  this doc.)

### 3. Pricing (display-only in the app; QuickBooks is the source of truth)
- `Order.total_price` is `product.price × quantity` at **list price**, computed
  in `Order.save()` when the order is placed or its product/quantity changes.
  Re-saving an order otherwise (e.g. a status change in the admin) keeps the
  total it was placed at, so a later price change never rewrites old orders.
- **Changing a price:** prices live on the `Product` rows, so change them with a
  data migration (see `0018_gift_jars_eight_dollars.py`, which set gift jars to
  $8). Storefront "$N each" copy reads the price, and descriptions don't repeat
  it, so nothing else needs editing.
- **Gift jar lineup:** Mini Favor Jar and Mini Holiday Jar (size "Mini", $8)
  and the larger **4 oz Gift Jar** ($10, added by
  `0019_add_four_oz_gift_jar.py`). When gift prices differ, the storefront copy
  reads "from $<lowest> each". A gift product with size "4 oz" falls back to the
  blue-ribbon photo in `_product_image.html`.
- A **seasonal promo** discount is display-only: the site shows the reduced
  price and the confirmation page shows the discount, but the stored total is
  **not** recomputed. The family applies the discount by hand on the invoice.
  See `docs/promotions.md`.
- **Postage** is not stored or calculated. Delivery orders show "before
  postage" and it's added by hand on the invoice; pickup orders show no postage.
- **Free shipping on large gift jar orders.** A delivered order of
  `FREE_SHIPPING_MIN_QUANTITY` (24, in `shop/models.py`) or more of a
  `category='gift'` product ships free (`Order.ships_free`). Full-size honey
  never qualifies. Because the self-serve cap is also 24, an online order
  qualifies at exactly 24; bigger orders go through the callback flow and are
  quoted by hand. The gift section, the "24" quantity option, the order
  summary, the live total, and the confirmation page all say so, and the Slack
  alert/admin email carry a **FREE SHIPPING** flag so postage is left off the
  invoice. Like the promo, nothing stored changes — it's applied by hand.
- The order form shows a **live running total** (JS) as product/quantity change,
  including the promo discount — purely informational.

### 4. Notification to the family (`notify_new_order`)
- Posts a Slack message via `post_message` (bot token → `chat.postMessage` so
  the message `ts` is recorded for reaction tracking; falls back to an incoming
  webhook if no bot token). Also sends an admin email (`send_admin_email`).
- The message includes customer name, phone, email, product × qty = total, and
  either **"Ship to: <address>"** (delivery) or **"Local pickup — arrange a
  pickup time"** (pickup), plus a nudge to send the QuickBooks invoice.
- A `📞 CALL BACK REQUESTED` flag appears when `prefer_callback` is set.
- A `🚚 FREE SHIPPING — don't add postage to the invoice` line appears when
  `order.ships_free` (see Pricing above).

### 5. Status tracking via Slack reactions (`shop/services/slack_events.py`)
The family drives status by adding emoji **reactions** to the order's Slack
message. Status is resolved from the *full set* of reactions present (not
per-event), so removing a reaction steps the status back. For `Order`:

| Reaction | Status |
|---|---|
| (none) | `pending` |
| 📦 `:package:` | `processing` |
| ✅ `:white_check_mark:` | `completed` |
| ❌ `:x:` | `cancelled` (terminal — overrides the rest) |

The bot replies in-thread confirming each status change. Status also syncs
Django → Slack via a `post_save` signal (`shop/signals.py`) so admin edits and
reactions stay consistent. Inbound events hit the `slack_events` endpoint
(request signature verified).

### 6. Reminders (`manage.py send_order_reminders`)
Nudges the family about orders still `pending`: unacknowledged orders older than
24h, and acknowledged-but-still-pending orders 24h after acknowledgement
(`acknowledged_at`, set from the admin). Sends via `notify_order_reminder` and
stamps `reminder_sent_at` so it doesn't repeat. Intended to run on a schedule.

## Spam protection (all public submission forms)

Every public form — orders, callbacks, nuc/pollination/bee-removal requests —
mixes in `AntiSpamMixin` (`shop/forms.py`) to keep scripted spam out of Slack.
Two low-friction, no-CAPTCHA traps, both invisible to real visitors:

- **Honeypot** — a hidden `website` field (rendered off-screen by
  `templates/shop/_anti_spam_fields.html`) that must stay empty. Bots fill every
  field, so any content here fails validation.
- **Submission timing** — a signed `loaded_at` render timestamp. A submission
  that arrives less than `MIN_FORM_FILL_SECONDS` (2s) after the page rendered is
  treated as scripted.

Both **fail open** when their signal is absent (missing/tampered/expired token),
so a genuine submission is never silently dropped; the honeypot is the always-on
backstop. When a trap fires the form is invalid — the record is **not** saved and
**no** Slack/email notification fires — exactly like any other validation error.
The include also renders `form.non_field_errors`, so a rejection shows a message
rather than failing silently. Tests: `shop/tests/test_antispam.py`.

If you add a new public form, inherit `AntiSpamMixin` **and** `{% include
'shop/_anti_spam_fields.html' %}` right after `{% csrf_token %}`, or it gets no
protection.

## Where things live

- Views: `shop/views.py` · Forms: `shop/forms.py` · Model: `shop/models.py`
  (`Order`)
- Notifications: `shop/services/notifications.py`
- Slack reaction → status: `shop/services/slack_events.py`, `shop/signals.py`
- Templates: `templates/shop/order_honey.html`, `order_success.html`
- Reminder job: `shop/management/commands/send_order_reminders.py`
- Tests: `shop/tests/test_order_flow.py`, `test_notifications.py`,
  `test_order_reminders.py`, `test_slack_reactions.py`

## When you change the ordering process

Update, in the same change: the code + its tests (see the testing policy in
`CLAUDE.md`), and **this runbook**. If you touch fulfillment, pricing, or
notifications, re-read sections 2–4 above and make sure they still describe
reality.
