# Django Blog Platform

[![CI](https://github.com/saqibnawab/django-blog/actions/workflows/ci.yml/badge.svg)](../../actions)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.2-092e20)
![DRF](https://img.shields.io/badge/DRF-3.17-a30000)

A full-stack, multi-user blog platform built with **Django 5** and **Django REST Framework**, featuring a JWT-secured REST API with interactive OpenAPI docs, PostgreSQL, Docker, a comprehensive test suite, and CI — alongside a server-rendered Tailwind CSS web interface.

## Features

### Web application
- **Authentication & authorization** — signup, login/logout, object-level permissions (only authors can edit/delete their posts)
- **Full CRUD** for blog posts with cover-image uploads
- **Draft / published workflow** — drafts are private to their author
- **Categories & tags** with filterable listing pages
- **Search** across titles, content, and tags
- **Comments and likes** on posts
- **Pagination** on all list pages
- Responsive UI built with **Tailwind CSS**

### REST API (`/api/`)
- **JWT authentication** (`/api/token/`, `/api/token/refresh/`) via SimpleJWT
- Full CRUD for posts; read/moderate-own for comments; read-only taxonomies
- Custom actions: `POST /api/posts/{id}/like/` (toggle), `POST /api/posts/{id}/comments/`
- **Filtering** (`?category__slug=`, `?tags__slug=`, `?author__username=`), **search** (`?search=`), and **ordering** (`?ordering=-created_at`)
- Draft visibility enforced at the queryset level — anonymous clients only ever see published posts
- **Rate throttling** for anonymous and authenticated users
- **Interactive OpenAPI 3 docs** (Swagger UI) at [`/api/docs/`](http://localhost:8000/api/docs/) via drf-spectacular

### Engineering
- **PostgreSQL** in production/Docker/CI, SQLite fallback for zero-config local dev (`DATABASE_URL`-driven via dj-database-url)
- **Docker** — multi-service `docker-compose` (app + Postgres) with health checks, non-root container user, gunicorn
- **59 tests** covering models, views, permissions, and every API endpoint
- **GitHub Actions CI** — system checks, migration drift detection, full test run against Postgres, and a Docker build
- **12-factor config** — all settings via environment variables, production security hardening (HSTS, secure cookies, SSL redirect)
- **WhiteNoise** for hashed/compressed static file serving

## Quick start

### Option 1 — Docker (recommended)

```bash
docker compose up --build
```

Then seed demo content (users, posts with images, comments, likes):

```bash
docker compose exec web python manage.py seed_demo
```

Open <http://localhost:8000>. Demo users: `alice` / `bob` / `carol`, password `demo-pass-1234`.

### Option 2 — Local virtualenv

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # optional demo content
python manage.py runserver
```

Uses SQLite by default; set `DATABASE_URL` to point at Postgres (see `.env.example`).

## Using the API

```bash
# Get a token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "demo-pass-1234"}'

# List posts (public)
curl "http://localhost:8000/api/posts/?search=django"

# Create a post (authenticated)
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello API", "content": "Posted via the REST API", "status": "published"}'

# Toggle a like
curl -X POST http://localhost:8000/api/posts/1/like/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Full interactive documentation: **<http://localhost:8000/api/docs/>**

## Running tests

```bash
python manage.py test
```

CI runs the same suite against PostgreSQL on every push and pull request.

## Project structure

```
django_practice/        # Project config (env-driven settings, root urls)
blog/
├── models.py           # Post, Category, Tag, Comment (+ likes M2M)
├── views.py            # Server-rendered views: CRUD, search, pagination
├── forms.py            # Post & comment ModelForms
├── api/                # REST API package
│   ├── serializers.py  # List/detail serializers, nested authors & comments
│   ├── views.py        # ViewSets with filtering, custom like/comment actions
│   ├── permissions.py  # IsAuthorOrReadOnly object-level permission
│   └── urls.py         # Router + JWT + OpenAPI endpoints
├── management/commands/seed_demo.py   # Demo data seeder
├── templates/          # Tailwind-styled server-rendered UI
└── tests/              # Model, view, and API test suites
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | Cryptographic signing key (set in production!) |
| `DJANGO_DEBUG` | `true` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DATABASE_URL` | SQLite | e.g. `postgres://user:pass@host:5432/db` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | Needed behind HTTPS proxies |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` (when `DEBUG=false`) | Force HTTPS |

## Deployment

The app is ready to deploy on any container platform (Render, Railway, Fly.io, AWS):

1. Provision a PostgreSQL database and set `DATABASE_URL`
2. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`
3. Deploy the Docker image — migrations run automatically on startup, static files are served by WhiteNoise

## Tech stack

Django 5.2 · Django REST Framework · SimpleJWT · drf-spectacular · django-filter · PostgreSQL · Docker · gunicorn · WhiteNoise · Tailwind CSS · GitHub Actions
