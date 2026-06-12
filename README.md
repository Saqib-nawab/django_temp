# Django Blog Platform

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.2-092e20)
![DRF](https://img.shields.io/badge/DRF-3.17-a30000)
![PostgreSQL](https://img.shields.io/badge/postgresql-16-336791)
![Docker](https://img.shields.io/badge/docker-ready-2496ed)
![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen)

A full-stack, multi-user blog platform built with **Django 5** and **Django REST Framework** — a server-rendered Tailwind CSS web app and a JWT-secured REST API with interactive OpenAPI documentation, backed by PostgreSQL, fully containerized with Docker, and covered by a 59-test suite running in GitHub Actions CI.

---

## Screenshots

### Home — post feed with categories, tags, search & pagination

Posts are displayed as cards with cover images, category badges, tag pills, and live like/comment counts. The header has a global search bar, and category chips filter the feed with post counts per category.

![Home page](docs/screenshots/home.png)

### Post detail — likes, comments, and author controls

Each post page shows the cover image, category and tags, a one-click **like toggle**, and a **comment thread**. Edit/Delete buttons appear only for the post's author — enforced server-side, not just hidden in the UI.

![Post detail page](docs/screenshots/post-detail.png)

### Search & filtering

Search matches across titles, content, **and tag names**. Results keep the category chips so you can drill down further, and active filters can be cleared with one click.

![Search results](docs/screenshots/search.png)

### Writing a post — drafts, images, taxonomy

The post editor supports cover image upload, category selection, multi-tag selection, and a **draft/published** workflow — drafts are visible only to their author, everywhere (web *and* API).

![New post form](docs/screenshots/new-post.png)

### REST API — interactive Swagger documentation

The entire API is documented with OpenAPI 3 and browsable at `/api/docs/`: JWT auth, full CRUD on posts, comment moderation, like toggling, filtering, search, and ordering.

![Swagger API docs](docs/screenshots/api-docs.png)

### Authentication

Signup with Django's validated password rules, login/logout, and session-based auth for the web UI (the API uses JWT instead).

![Signup page](docs/screenshots/signup.png)

---

## Features

### Web application
- **Authentication & authorization** — signup, login/logout, and object-level permissions: only authors can edit or delete their own posts
- **Full CRUD** for posts with cover-image uploads
- **Draft / published workflow** — drafts are private to their author
- **Categories & tags** with filterable list pages
- **Search** across titles, content, and tags
- **Comments & likes** on every post
- **Pagination** on all list pages
- Responsive UI with **Tailwind CSS**

### REST API (`/api/`)
- **JWT authentication** via SimpleJWT (`POST /api/token/`, `POST /api/token/refresh/`)
- Full CRUD for posts; authors moderate their own comments; read-only taxonomy endpoints
- Custom actions: `POST /api/posts/{id}/like/` (toggle) and `POST /api/posts/{id}/comments/`
- **Filtering** (`?category__slug=`, `?tags__slug=`, `?author__username=`), **search** (`?search=`), **ordering** (`?ordering=-created_at`)
- Draft visibility enforced at the queryset level — anonymous clients can never see drafts
- **Rate throttling** for anonymous and authenticated clients
- **OpenAPI 3 schema + Swagger UI** via drf-spectacular

### Engineering
- **PostgreSQL** in Docker and CI, with a zero-config SQLite fallback for local development (`DATABASE_URL`-driven via dj-database-url)
- **Docker** — `docker compose up` brings up the app (gunicorn, non-root user) and Postgres 16 with health checks; migrations run automatically on startup
- **59 tests** covering models, views, permissions, and every API endpoint — run against PostgreSQL in CI
- **GitHub Actions CI** — system checks, migration-drift detection, the full test suite, and a Docker image build on every push
- **12-factor configuration** — every setting comes from environment variables; production hardening (HSTS, secure cookies, SSL redirect) activates automatically when `DEBUG=false`
- **WhiteNoise** serving hashed, compressed static files

## Quick start

### Option 1 — Docker (one command)

```bash
docker compose up --build
```

Seed demo content (3 users, 8 posts with cover images, comments, likes):

```bash
docker compose exec web python manage.py seed_demo
```

Open <http://localhost:8000> — demo users `alice` / `bob` / `carol`, password `demo-pass-1234`.

### Option 2 — Local virtualenv

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # optional demo content
python manage.py runserver
```

SQLite is used by default; set `DATABASE_URL` to use Postgres (see `.env.example`).

## Using the API

```bash
# Get a JWT
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "demo-pass-1234"}'

# List & search posts (public)
curl "http://localhost:8000/api/posts/?search=django"

# Create a post
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello API", "content": "Posted via the REST API", "status": "published"}'

# Toggle a like
curl -X POST http://localhost:8000/api/posts/1/like/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Interactive docs with a built-in API client: `http://localhost:8000/api/docs/`

## Running tests

```bash
python manage.py test
```

The same suite runs against PostgreSQL in CI on every push and pull request.

## Project structure

```
django_practice/        # Project config (env-driven settings, root urls)
blog/
├── models.py           # Post, Category, Tag, Comment (+ likes M2M, auto-slugs)
├── views.py            # Server-rendered views: CRUD, search, pagination
├── forms.py            # Post & comment ModelForms
├── api/                # REST API package
│   ├── serializers.py  # List/detail serializers, nested authors & comments
│   ├── views.py        # ViewSets with filtering + custom like/comment actions
│   ├── permissions.py  # IsAuthorOrReadOnly object-level permission
│   └── urls.py         # Router + JWT + OpenAPI endpoints
├── management/commands/seed_demo.py   # Demo data seeder
├── templates/          # Tailwind-styled server-rendered UI
└── tests/              # Model, view, and API test suites (59 tests)
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | Cryptographic signing key (set in production!) |
| `DJANGO_DEBUG` | `true` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DATABASE_URL` | SQLite | e.g. `postgres://user:pass@host:5432/db` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | Needed behind HTTPS proxies |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` (when `DEBUG=false`) | Force HTTPS |

## Tech stack

Django 5.2 · Django REST Framework · SimpleJWT · drf-spectacular · django-filter · PostgreSQL · Docker · gunicorn · WhiteNoise · Tailwind CSS · GitHub Actions
