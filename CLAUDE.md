# CLAUDE.md

Guidance for working in this repository. Read this before making changes.

## Project

Django 6.0 site for **Bear Creek Apiaries & Honey LLC** — a small family honey
business. Customers browse honey/gift jars, place orders, and submit service
requests (bee nucs, pollination, bee removal, callbacks). Orders are fulfilled
manually via QuickBooks invoices; submissions fire Slack notifications. Hosted
on Render; SQLite database.

- App code: `shop/` (models, views, forms, admin, services, sitemaps).
- Project config: `bearcreek/`.
- Templates: `templates/shop/`; static assets: `static/`.
- Product/order inventory lives in the **gitignored** SQLite DB. Seed/changes
  for production go through a **data migration** (see
  `shop/migrations/0011_seed_live_catalog.py`), not manual prod edits.

## Testing policy (required)

These rules are mandatory, not optional:

1. **Every change to logic or behavior MUST come with tests.** If you add or
   change a view, form, model method, validation rule, workflow, or
   notification, add or update tests in `shop/tests/` that prove the new
   behavior and guard against regressions. A logic change without a
   corresponding test is incomplete.
2. **Run the full suite after every change** and make it pass before you
   consider the work done or commit:
   ```
   python manage.py test
   ```
   Do not run only the file you touched — run everything, so cross-cutting
   regressions surface.
3. **Bug fixes start with a test** that reproduces the bug (fails before the
   fix, passes after).
4. Keep tests fast and hermetic: mock external calls (Slack/email via
   `unittest.mock`), never hit the network, and rely on Django's test DB.

The repo enforces this with gates (see below), but do not wait for the gate —
run the tests yourself.

## Quality gates

- `pre-commit` runs ruff + `manage.py check` + missing-migration check on every
  commit, and the **full test suite on pre-push**.
- GitHub Actions (`.github/workflows/ci.yml`) runs the same checks on push/PR.
- Setup once per clone (inside your venv):
  ```
  pip install -r requirements-dev.txt
  pre-commit install
  pre-commit install --hook-type pre-push
  ```

## Conventions

- Function-based views in `shop/views.py`; `ModelForm`s in `shop/forms.py`
  (share `ContactValidationMixin` for phone/email normalization).
- Business logic helpers live in `shop/services/` (e.g. `notifications.py`);
  keep heavy logic out of views.
- Schema changes need a migration; run `python manage.py makemigrations`.
- Never hardcode URLs — use `reverse()` / `{% url %}`.
- Self-serve order quantity is capped (`MAX_SELF_SERVE_QUANTITY` in
  `shop/forms.py`); larger orders are routed to the callback flow.
- "Please call" / "call for pricing" prompts should route to the callback
  request form so the business gets a Slack notification.
- **Seasonal promotions** are date-gated and display-only — see
  `docs/promotions.md` before adding/changing a sale. The promo retires itself
  after `PROMO_BANNER_END`; the discount is shown on the site but applied by
  hand on the QuickBooks invoice (no stored order total is recomputed).

## Handy commands

```
python manage.py runserver        # dev server
python manage.py test             # full test suite (run after every change)
python manage.py migrate          # apply migrations
ruff check .                      # lint
pre-commit run --all-files        # run all hooks across the repo
```
