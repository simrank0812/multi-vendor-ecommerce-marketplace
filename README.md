# Multi-Vendor E-Commerce Marketplace (Django)

A web-based marketplace where many sellers list products and customers buy from different stores in one cart.
Stack: **Python Django · HTML/CSS/JavaScript · SQLite**

## Run it
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo     # optional demo data
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Demo logins (after `seed_demo`)
| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Seller (approved) | seller1 / seller2 | seller123 |
| Seller (pending) | seller3 | seller123 |
| Customer | customer1 | customer123 |

## Features by role
**Customer** – browse, live search, category + price filters, sorting, pagination, AJAX add-to-cart, quantity controls, checkout with stock validation, order tracking timeline, cancel item, return request.
**Seller** – registration (needs admin verification), dashboard with sales chart/low-stock/top products, product CRUD with image upload, quick stock update, process orders (placed → processing → shipped → delivered), approve/reject returns.
**Admin** – verify/reject sellers, set per-seller commission %, hide/show products, monitor all orders, commission report. (Built-in Django admin also at `/django-admin/`.)

## Project structure
```
config/     settings, urls
accounts/   custom User (role), SellerProfile, register/login
store/      models (Product, Cart, Order, OrderItem, ReturnRequest), customer/seller/admin views
templates/  HTML pages     static/  css + js
```
## Key design points (for viva)
- `OrderItem` stores price, commission rate and commission amount **at purchase time**, so later price/commission changes do not alter old orders.
- Checkout runs in `transaction.atomic()` with `select_for_update()` to prevent overselling.
- `role_required` decorator enforces Admin / Seller / Customer access; sellers need `approved` status.
- Cancelled and returned items are excluded from sales and commission totals; stock is restored.
