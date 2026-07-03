# Growth & discoverability features

Programmatic ways the site helps drive traffic and orders. All of these read the
**live catalog** (`Product`), so they stay in sync automatically — there is
nothing to regenerate when the catalog changes.

## Product structured data (rich results)

Each product detail page emits schema.org `Product` + `Offer` JSON-LD
(`shop/services/structured_data.py::product_jsonld`, rendered into the
`structured_data` block of `base.html`). This makes jars eligible for Google's
free product rich results (price + availability shown in search). The advertised
price includes any active promo discount (display-only; the QuickBooks invoice
stays the financial source of truth).

## Google Merchant Center feed

`/feed.xml` (`shop/views.py::product_feed`) is an RSS 2.0 + `g:` namespace feed
of all **in-stock** products, for free Google Shopping listings.

One-time setup by the site owner:

1. Create a free Google Merchant Center account and verify/claim the site
   (the domain is already the one in the business's Google Business Profile).
2. Products → Feeds → add a **scheduled feed** pointing at
   `https://<the-site>/feed.xml`, fetched daily.
3. Opt into "free listings." No ad spend required.

Because the feed is generated on request, edits in the admin (price, stock,
new jars) show up on Google's next scheduled fetch with no manual export.

## Review QR card (`/review`)

`shop/views.py::review_card` renders a shareable, printable card at
`/review` with a QR code that opens the Google review page in one tap — for the
farmers market, jar labels, or texting to customers. The visible link comes from
`settings.GOOGLE_REVIEW_URL`; the QR image is `static/images/review-qr.png`.

**If `GOOGLE_REVIEW_URL` ever changes, regenerate the QR image** so it still
matches (it's a plain QR encoding of that URL — any QR generator works; this one
was made with `segno`, which is not a project dependency). The standalone assets
also live in `marketing/` (not required for the site to work).

## Ordering friction reducers

- **Pickup vs. delivery** toggle on the order form — local-pickup customers no
  longer have to enter a shipping address (`OrderForm`, `Order.fulfillment`).
- **Live running total** on the order form, including the promo discount, so
  customers see the price before submitting.

See also `docs/promotions.md` for the seasonal-promo mechanics referenced above.
