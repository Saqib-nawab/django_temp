"""Seed the database with realistic demo content for the blog.

Creates demo users, categories, tags, posts (with cover images downloaded
from picsum.photos), comments, and likes. Safe to re-run: it skips seeding
if demo content already exists unless --force is passed.
"""

import random
import urllib.request

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from blog.models import Category, Comment, Post, Tag

User = get_user_model()

DEMO_PASSWORD = "demo-pass-1234"

USERS = ["alice", "bob", "carol"]

CATEGORIES = ["Web Development", "Data Science", "DevOps", "Career"]

TAGS = ["python", "django", "rest-api", "docker", "postgresql", "testing", "deployment", "beginners"]

POSTS = [
    {
        "title": "Building a REST API with Django REST Framework",
        "category": "Web Development",
        "tags": ["python", "django", "rest-api"],
        "content": (
            "Django REST Framework (DRF) is the de facto standard for building APIs in Django. "
            "In this post we walk through serializers, viewsets, and routers, and show how they "
            "work together to expose a clean, browsable API with very little boilerplate.\n\n"
            "We start by defining serializers that translate model instances to JSON, then wire "
            "up viewsets that handle the full CRUD lifecycle. Routers generate the URL patterns "
            "automatically, so adding a new resource is often just three lines of code.\n\n"
            "Finally we cover authentication with JWT tokens, object-level permissions so users "
            "can only edit their own content, and throttling to protect the API from abuse."
        ),
    },
    {
        "title": "Why PostgreSQL Should Be Your Default Database",
        "category": "DevOps",
        "tags": ["postgresql", "django"],
        "content": (
            "SQLite is great for development, but production workloads need a real database "
            "server. PostgreSQL brings proper concurrency, rich data types, full-text search, "
            "and battle-tested reliability.\n\n"
            "Switching Django to Postgres is painless: install psycopg2, set DATABASE_URL, and "
            "run your migrations. With dj-database-url the same settings file works locally "
            "with SQLite and in production with Postgres.\n\n"
            "We also look at connection pooling with conn_max_age and why you should always "
            "run the same database in CI that you run in production."
        ),
    },
    {
        "title": "Dockerizing a Django Application: A Practical Guide",
        "category": "DevOps",
        "tags": ["docker", "django", "deployment"],
        "content": (
            "Containers make 'works on my machine' a thing of the past. In this guide we write "
            "a production-ready Dockerfile for Django: a slim Python base image, layer-cached "
            "dependency installation, a non-root user, and gunicorn as the WSGI server.\n\n"
            "docker-compose ties it together with a PostgreSQL service, health checks, and "
            "volume mounts so your data survives container restarts.\n\n"
            "The result: one command — docker compose up — and anyone can run your entire "
            "stack, identical to production."
        ),
    },
    {
        "title": "Test-Driven Development in Django: Where to Start",
        "category": "Web Development",
        "tags": ["testing", "django", "python", "beginners"],
        "content": (
            "Tests are the difference between a tutorial project and an engineering project. "
            "Django ships with a powerful test framework built on unittest, with a test client "
            "that can simulate full request/response cycles.\n\n"
            "Start with model tests (does the slug auto-generate? does ordering work?), then "
            "view tests (does an anonymous user get redirected? can a user edit someone "
            "else's post?), then API tests for every endpoint.\n\n"
            "A CI pipeline that runs the suite on every push keeps regressions out of main."
        ),
    },
    {
        "title": "From Jupyter Notebooks to Production Models",
        "category": "Data Science",
        "tags": ["python", "deployment"],
        "content": (
            "The gap between a notebook that works and a model serving real traffic is wide. "
            "This post covers the journey: refactoring exploratory code into modules, "
            "pinning dependencies, and wrapping inference in a web API.\n\n"
            "We discuss model versioning, input validation, and monitoring — the unglamorous "
            "parts that make machine learning actually useful in production.\n\n"
            "Spoiler: most of the work is software engineering, not data science."
        ),
    },
    {
        "title": "How I Structure My Django Projects in 2026",
        "category": "Web Development",
        "tags": ["django", "python"],
        "content": (
            "After years of Django projects, here is the layout I keep coming back to: apps "
            "that own their models, templates, and API modules; settings driven entirely by "
            "environment variables; and a thin project package that just wires things "
            "together.\n\n"
            "Keep business logic in models and managers, keep views thin, and put the API in "
            "its own package inside each app (serializers.py, views.py, permissions.py, "
            "urls.py). Future you will thank present you.\n\n"
            "And always, always write a README that lets someone run the project in one "
            "command."
        ),
    },
    {
        "title": "Landing Your First Backend Developer Job",
        "category": "Career",
        "tags": ["beginners", "python"],
        "content": (
            "Portfolios beat certificates. A single well-built project — with authentication, "
            "a documented REST API, tests, and a live deployment — tells a hiring manager more "
            "than a dozen course completions.\n\n"
            "Make your GitHub README excellent: screenshots, an architecture overview, setup "
            "instructions, and a link to the live demo. Write commit messages like someone "
            "will read them, because someone will.\n\n"
            "Then practice talking about your decisions: why Postgres, why JWT, why Docker. "
            "Interviews reward people who understand their own stack."
        ),
    },
    {
        "title": "Full-Text Search in Django Without Elasticsearch",
        "category": "Web Development",
        "tags": ["django", "postgresql", "rest-api"],
        "content": (
            "You probably don't need Elasticsearch. For most applications, Django's ORM gets "
            "you surprisingly far: icontains lookups for simple cases, and PostgreSQL's "
            "SearchVector / SearchRank for proper ranked full-text search.\n\n"
            "We benchmark both approaches on a realistic dataset and show when each one makes "
            "sense. Spoiler: under a few hundred thousand rows, Postgres full-text search is "
            "fast, free, and operationally simple.\n\n"
            "Keep your architecture boring until the data forces you to do otherwise."
        ),
    },
]

COMMENTS = [
    "Great write-up, this clarified a lot for me!",
    "I tried this on my own project and it worked perfectly. Thanks!",
    "Could you do a follow-up on deployment to Render or Fly.io?",
    "Bookmarked. The section on permissions was exactly what I needed.",
    "Nice post — one suggestion: mention select_related for the N+1 queries.",
    "This is the clearest explanation of this topic I've found.",
    "How would this change with async views?",
]


class Command(BaseCommand):
    help = "Seed the database with demo users, posts, comments, and likes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Seed even if demo content already exists.",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip downloading cover images (faster, works offline).",
        )

    def handle(self, *args, **options):
        if Post.objects.filter(author__username__in=USERS).exists() and not options["force"]:
            self.stdout.write(self.style.WARNING("Demo content already exists; use --force to reseed."))
            return

        random.seed(42)

        users = []
        for username in USERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users.append(user)
        self.stdout.write(f"Users ready: {', '.join(USERS)} (password: {DEMO_PASSWORD})")

        categories = {name: Category.objects.get_or_create(name=name)[0] for name in CATEGORIES}
        tags = {name: Tag.objects.get_or_create(name=name)[0] for name in TAGS}
        self.stdout.write(f"Created {len(categories)} categories and {len(tags)} tags.")

        for index, data in enumerate(POSTS):
            author = users[index % len(users)]
            post, created = Post.objects.get_or_create(
                title=data["title"],
                defaults={
                    "content": data["content"],
                    "author": author,
                    "category": categories[data["category"]],
                    "status": Post.Status.PUBLISHED,
                },
            )
            if not created:
                continue
            post.tags.set(tags[t] for t in data["tags"])

            if not options["skip_images"]:
                try:
                    url = f"https://picsum.photos/seed/{post.slug}/900/450"
                    with urllib.request.urlopen(url, timeout=15) as response:
                        post.image.save(f"{post.slug}.jpg", ContentFile(response.read()), save=True)
                    self.stdout.write(f"  ↳ image downloaded for '{post.title}'")
                except Exception as exc:  # network failures should not abort seeding
                    self.stdout.write(self.style.WARNING(f"  ↳ image skipped for '{post.title}': {exc}"))

            for commenter in random.sample(users, k=random.randint(1, len(users))):
                if commenter != author:
                    Comment.objects.create(
                        post=post, author=commenter, body=random.choice(COMMENTS)
                    )

            for liker in random.sample(users, k=random.randint(0, len(users))):
                post.likes.add(liker)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(POSTS)} posts with comments and likes."))
