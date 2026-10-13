# LumaCart — Production-Ready Luxury Fashion E-Commerce

LumaCart is a high-performance, full-stack fashion e-commerce platform built with Python Django 5, Django REST Framework, PostgreSQL, Django Channels (WebSockets), Redis, Celery, Razorpay payment gateway integration, and a modern vanilla HTML5/CSS3/JavaScript frontend.

---

## 💎 Design Philosophy & UI/UX

- **Aesthetic**: Minimal luxury fashion aesthetic inspired by Nordic and Mediterranean ateliers.
- **Base Palette**: Warm white and ivory base (`#FAF9F6`), with subtle accents of soft beige (`#EFEBE4`), muted sage (`#8A9A86`), dusty rose (`#D8A49B`), and deep charcoal text (`#1F1F1F`).
- **No Black Theme**: Zero dark/black backgrounds; every storefront and dashboard view maintains light, spacious, breathable typography with rounded cards and soft natural shadows.
- **Auth Experience**: Crisp white floating cards set against high-resolution editorial fashion collages showcasing apparel, fine jewellery, shoes, and leather bags.

---

## ⚙️ Architecture & Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Semantic HTML5, Vanilla CSS3 (Custom Design System), Modern Vanilla ES6+ Modules |
| **Backend** | Python Django 5.x & Django REST Framework |
| **Database** | **PostgreSQL Only** (with JSONField, row-level locking `select_for_update()`, check constraints) |
| **Authentication**| Django Custom User Model (`CustomUser`) with JWT (`SimpleJWT`) |
| **Realtime** | Django Channels 4 & Daphne ASGI server (WebSockets for stock availability and order status updates) |
| **Background Tasks** | Celery 5.x with Redis broker |
| **Payments** | Real Razorpay integration with server-side HMAC-SHA256 signature verification |
| **Containerization** | Docker & Docker Compose (PostgreSQL 16, Redis 7, Daphne, Celery) |

---

## 📂 Project Structure

```
LumaCart/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py       # Production & dev configuration
│   │   ├── urls.py           # Master routing
│   │   ├── asgi.py           # Daphne ASGI & Channels router
│   │   ├── wsgi.py           # WSGI router
│   │   └── celery.py         # Celery broker configuration
│   └── apps/
│       ├── accounts/         # CustomUser, Address, JWT Auth
│       ├── catalog/          # Products, Categories, Brands, Variants, Inventory, Seed Command
│       ├── cart/             # Database-backed Cart, CartItem, Coupons
│       ├── orders/           # Order, OrderItem, Status workflow, Analytics
│       ├── payments/         # Razorpay client, verification, Payment model
│       ├── reviews/          # Verified buyer reviews & moderation
│       └── notifications/    # Channels WebSocket consumers & notifications
├── frontend/
│   ├── index.html            # Dynamic Storefront Homepage
│   ├── css/
│   │   ├── theme.css         # Palette, typography, variables
│   │   ├── base.css          # Utilities, buttons, forms, skeletons
│   │   ├── components.css    # Header, navigation, product cards, footer
│   │   ├── auth.css          # Auth panel & editorial collage
│   │   └── pages.css         # Catalog, details, cart, checkout, admin
│   ├── js/
│   │   ├── config.js         # API & WebSocket endpoints
│   │   └── modules/
│   │       ├── apiClient.js  # JWT fetch wrapper, 401 refresh, session handling
│   │       ├── auth.js       # User session & nav sync
│   │       ├── cart.js       # DB cart operations, badges, coupons
│   │       ├── wishlist.js   # Wishlist state manager
│   │       ├── websocket.js  # Live inventory & order updates
│   │       └── ui.js         # Navigation, cards, shell generator
│   └── pages/
│       ├── products.html     # Catalog with debounced search & filters
│       ├── product-detail.html # Gallery, variants, stock limits, verified reviews
│       ├── cart.html         # Bag with server-side calculations
│       ├── checkout.html     # Address selection, Razorpay modal
│       ├── order-confirmation.html # Order invoice & receipt
│       ├── orders.html       # Customer order history
│       ├── order-detail.html # Live tracking timeline & cancellation
│       ├── wishlist.html     # Saved items
│       ├── profile.html      # Account details & addresses
│       ├── login.html        # Sign in
│       ├── register.html     # Create account
│       ├── forgot-password.html
│       ├── reset-password.html
│       └── admin.html        # Staff portal (inventory editor, orders, CSV)
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Local Development Instructions

### 1. Environment Configuration

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Key environment variables:
- `DJANGO_SECRET_KEY`: High-entropy production key.
- `DEBUG`: Set to `True` for dev, `False` for production.
- `DATABASE_URL`: `postgresql://postgres:postgres@localhost:5432/lumacart_db`
- `POSTGRES_DB`: `lumacart_db`
- `POSTGRES_USER`: `postgres`
- `POSTGRES_PASSWORD`: `postgres`
- `POSTGRES_HOST`: `localhost`
- `POSTGRES_PORT`: `5432`
- `RAZORPAY_KEY_ID`: Your Razorpay Key ID (default test key included).
- `RAZORPAY_KEY_SECRET`: Your Razorpay Key Secret.
- `REDIS_URL`: `redis://localhost:6379/0`

### 2. Installing Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Setting Up PostgreSQL Database

In PostgreSQL (via `psql` or pgAdmin):
```sql
CREATE DATABASE lumacart_db;
CREATE USER postgres WITH ENCRYPTED PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE lumacart_db TO postgres;
```

### 4. Running Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 5. Seeding Demo Fashion Data

Populates realistic luxury fashion products (linen coats, silk dresses, 18k gold pendants, nappa loafers, crescent bags), variants, stock inventory, discount coupons, and demo accounts into PostgreSQL:

```bash
python manage.py seed_demo_data
```

**Demo Credentials Seeded:**
- **Staff / Admin Account:**
  - Email: `admin@lumacart.com`
  - Password: `Admin@12345`
- **Customer Account:**
  - Email: `customer@lumacart.com`
  - Password: `Customer@12345`

### 6. Starting Services

#### Terminal 1: Django Backend (Daphne with HTTP & WebSockets)
```bash
python manage.py runserver 8000
# Or using Daphne ASGI for full WebSocket capability:
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

#### Terminal 2: Redis & Celery (Optional for Async Jobs)
```bash
# Start Redis
redis-server

# Start Celery Worker
celery -A config worker --loglevel=info
```

#### Accessing the Storefront:
Open `http://127.0.0.1:8000/index.html` in your browser. All API endpoints and static assets are served directly through the Daphne server.

---

## 🐳 Docker & Docker Compose Deployment

To build and run the entire stack (PostgreSQL 16, Redis 7, Daphne ASGI, Celery, Static files) in isolated containers:

```bash
cd infra
docker compose up --build -d
```

To run migrations and seed data inside the container:
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo_data
```

The application is now live at `http://localhost:8000`.

---

## 🧪 Automated Testing

Run the automated test suite covering authentication, permissions, stock validation, guest cart merge, checkout, Razorpay signature verification, race condition protection, and duplicate payments:

```bash
cd backend
python manage.py test apps
```

---

## 🔒 Security Best Practices Implemented

1. **Cryptographic Payment Signature Verification**: Every Razorpay order is verified server-side with HMAC SHA256 before inventory is reduced or orders confirmed.
2. **Row-Level Locking**: `select_for_update()` and `transaction.atomic()` prevent inventory overselling and race conditions during high-volume flash sales.
3. **JWT Rotation**: Access tokens expire after 4 hours; refresh tokens rotate automatically on refresh and are blacklisted upon rotation.
4. **Data Isolation**: Custom DRF permissions verify that users can never view or modify other users' carts, addresses, payments, or orders.
5. **No Secrets Committed**: All credentials and API keys are strictly configured through environment variables.
