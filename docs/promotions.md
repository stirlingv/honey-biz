# Running a seasonal promotion

The site has a small, reusable promo system (first built for the 2026 4th of
July sale). It is **date-gated** and **display-only** — read both ideas before
running a new promo.

## The two core ideas

1. **Date-gated = it retires itself.** A promo only renders while today is
   inside a start/end window. When the window closes, every promo element
   disappears on its own — no edit, no deploy, no "remember to take the banner
   down." You never have to call a developer to *end* a sale.

2. **Display-only = the invoice is still the source of truth.** The site takes
   no online payment; orders are fulfilled by a manual QuickBooks invoice. The
   discount is shown to the customer but **applied by hand on the invoice**. We
   deliberately do *not* recompute or store a discounted order total, and we do
   *not* change the Slack notification amount. That keeps one source of truth
   (the invoice) and avoids numbers that can drift apart.

   > ⚠️ **Manual step:** because it's display-only, whoever creates the invoice
   > must remember to subtract the discount. The customer's confirmation says
   > "applied on your invoice," so the site is making a promise a human keeps.

## What shows up when a promo is active

| Element | Where | File |
| --- | --- | --- |
| Announcement bar (every page) | top of `<body>` | `templates/base.html` |
| Holiday graphic + CTA | home page, under the hero | `templates/shop/home.html` |
| Struck-through list price + sale price + "$X off" tag | honey cards, gift cards | `templates/shop/products.html` |
| Same sale price treatment | product detail page | `templates/shop/product_detail.html` |
| Sale unit price + discount note | order form summary | `templates/shop/order_honey.html` |
| Per-order discount line | order confirmation | `templates/shop/order_success.html` |

All of them are wrapped in `{% if promo_active %}` / `{% if promo_active and
promo_discount %}`, so they appear and vanish together.

## How it works under the hood

- **Settings** (`bearcreek/settings.py`) — three knobs, all env-overridable:
  - `PROMO_BANNER_START` (YYYY-MM-DD) — first day the promo shows. May be empty.
  - `PROMO_BANNER_END` (YYYY-MM-DD) — last day, **inclusive**. Empty = promo off.
  - `PROMO_DISCOUNT_PER_JAR` — dollars off each jar (e.g. `2`).
- **Context processor** (`shop/context_processors.py`) — computes
  `promo_active` and `promo_discount` for every template. `promo_is_active()`
  is the single source of the date check (the order-confirmation view imports it
  too). Uses the server's local date.
- **Template filter** (`shop/templatetags/promo_extras.py`) — `sale_price`
  subtracts the discount from a price, floored at $0.
- **Tests** (`shop/tests/test_promo_banner.py`) — cover active/before/after the
  window, the inclusive final day, the disabled state, the `sale_price` filter,
  and the discounted display on the product list and confirmation.

## Starting a new promo

You can do it two ways:

### Option A — env vars only (no code change, fastest)
Set these on Render (or in `.env` locally) and restart:
```
PROMO_BANNER_START=2026-11-25
PROMO_BANNER_END=2026-11-30
PROMO_DISCOUNT_PER_JAR=3
```
This reuses the existing 4th-of-July copy and graphic, which won't fit a
different holiday — so Option A is best for *extending/shortening/ending* the
current promo, not for a brand-new themed one.

### Option B — a real new promo (code change)
1. Update the default dates and discount in `bearcreek/settings.py`.
2. Swap the copy and graphic:
   - Bar text in `templates/base.html`.
   - Headline/body/eyebrow + image in `templates/shop/home.html`
     (`promo-feature` section).
   - The "$X off through <date>" wording on `product_detail.html`, and the
     date in the order-form note (`order_honey.html`).
   - Add the new graphic to `static/images/live_photos/` (export a real web
     image — a `.png.pdf` won't load as an `<img>`; convert to JPG/PNG ~1200px).
3. Run the suite (`python manage.py test`) and update the promo tests if you
   changed wording the tests assert on (e.g. "July 5", "$2").

## Ending / changing a promo

- **Let it expire:** do nothing. After `PROMO_BANNER_END` it's gone.
- **End it early:** set `PROMO_BANNER_END` to a past date, or empty, via env —
  takes effect immediately, no deploy.
- **Extend it:** push `PROMO_BANNER_END` out via env.

## Gotchas

- Edit `PROMO_DISCOUNT_PER_JAR` while the dev server is running and you may see a
  one-reload error if you add the value before its import lands — it's just the
  StatReloader catching a mid-save file; the next reload is clean.
- Prices render with `floatformat:"-2"` in promo blocks, so whole-dollar prices
  show as `$15` not `$15.00`. Cents are preserved if a price has them.
- The styling (`.promo-bar`, `.promo-feature`, `.price-original`, `.price-sale`,
  `.promo-tag`) lives at the bottom of `static/css/style.css`.
