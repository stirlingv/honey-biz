# Bear Creek Apiaries & Honey LLC

A Django-based website for Bear Creek Apiaries & Honey LLC, a local honey business offering pure, natural honey and bee starter kits (nucs).

## Features

- **Product Catalog**: Browse and view details of various honey products
- **Online Ordering**: Submit honey orders with delivery information
- **Nuc Requests**: Request bee starter kits for aspiring beekeepers
- **About Page**: Learn about the business and sustainable beekeeping practices
- **Responsive Design**: Mobile-friendly HTML5 responsive design
- **Admin Interface**: Manage products, orders, and nuc requests

## Technology Stack

- **Backend**: Django 6.0
- **Database**: SQLite (development)
- **Frontend**: HTML5, CSS3
- **Python**: 3.12+

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd honey-biz
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Load sample product data:
```bash
python manage.py load_products
```

6. Create a superuser account (for admin access):
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the website at `http://localhost:8000`

### Admin Access

- Admin panel: `http://localhost:8000/admin/`
- Use the superuser credentials created in step 6

## Project Structure

```
honey-biz/
├── bearcreek/          # Django project settings
├── shop/               # Main application
│   ├── models.py       # Database models (Product, Order, NukeRequest)
│   ├── views.py        # View functions
│   ├── forms.py        # Django forms
│   ├── admin.py        # Admin interface configuration
│   └── urls.py         # URL routing
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   └── shop/           # Shop app templates
├── static/             # Static files (CSS, JS, images)
│   └── css/
│       └── style.css   # Main stylesheet
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Models

### Product
- Honey products with name, description, price, size, and stock status
- Optional product images

### Order
- Customer orders for honey products
- Tracks customer info, delivery address, product, quantity, and order status

### NukeRequest
- Requests for bee starter kits (nucs)
- Captures customer info, quantity, experience level, and preferred pickup date

## Usage

### For Customers

1. **Browse Products**: Visit the home page or products page to see available honey
2. **Order Honey**: Fill out the order form with your details and product selection
3. **Request Nucs**: Submit a nuc request form to inquire about bee starter kits
4. **Learn More**: Read the About page to learn about sustainable beekeeping

### For Administrators

1. Log in to the admin panel at `/admin/`
2. Manage products, orders, and nuc requests
3. Update order statuses and respond to customer inquiries
4. Add or modify product listings

## Development

To make changes to the website:

1. Models: Edit `shop/models.py` and run migrations
2. Views: Update `shop/views.py` for business logic
3. Templates: Modify files in `templates/shop/`
4. Styles: Edit `static/css/style.css`

After making changes, test locally before deploying.

## License

Copyright © 2024 Bear Creek Apiaries & Honey LLC. All rights reserved.
