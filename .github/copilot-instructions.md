# Copilot Instructions for Bear Creek Apiaries & Honey LLC

## Project Overview
- **Django 6.0** project for a local honey business: product catalog, online ordering, nuc (bee starter kit) requests, and admin management.
- Main app: `shop/` (models, views, forms, admin, URLs). Project config: `bearcreek/`.
- Data: SQLite (dev), models for Product, Order, NukeRequest.
- Templates: `templates/shop/` (customer-facing), `templates/admin/shop/order/` (admin customizations).
- Static assets: `static/` (CSS, images).

## Key Workflows
- **Setup:**
  - `python3 -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt`
  - `python manage.py migrate`
  - `python manage.py load_products` (loads sample data)
  - `python manage.py createsuperuser`
- **Run dev server:** `python manage.py runserver`
- **Admin:** `/admin/` (manage products, orders, nuc requests)
- **Tests:** Place in `shop/tests/` (pytest or Django test runner)
- **Custom management commands:** in `shop/management/commands/` (e.g., `load_products`, `send_order_reminders`)

## Patterns & Conventions
- **Models:** All business data in `shop/models.py`. Use Django migrations for schema changes.
- **Views:** Use function-based views in `shop/views.py`. Forms in `shop/forms.py`.
- **Templates:** Extend `base.html`. Use `{% url %}` for navigation. Customer and admin templates are separated.
- **Static:** Place CSS in `static/css/`, images in `static/images/`.
- **Fixtures:** Sample data in `shop/fixtures/initial_products.json`.
- **Services:** Business logic helpers in `shop/services/` (e.g., notifications, QuickBooks integration).

## Integration Points
- **QuickBooks:** See `shop/services/quickbooks.py` for accounting integration.
- **Notifications:** Email/SMS logic in `shop/services/notifications.py`.
- **Procfile/render.yaml:** For deployment (e.g., Render.com). Use `start.sh` for custom startup.

## Project-Specific Notes
- Use `Order` and `NukeRequest` for all customer-facing forms; do not create new models for similar flows.
- Management commands are the preferred way to automate admin tasks (see `shop/management/commands/`).
- All admin customizations go in `shop/admin.py` and `templates/admin/shop/order/`.
- Do not hardcode URLs; use Django's `reverse` or `{% url %}`.
- Keep business logic out of views—use services/helpers where possible.

## References
- [README.md](../../README.md) for setup, model, and usage details.
- Example: To add a new product type, update `shop/models.py`, create a migration, and add admin support in `shop/admin.py`.

---

If unsure about a workflow or pattern, check for similar examples in `shop/` or ask for clarification.
