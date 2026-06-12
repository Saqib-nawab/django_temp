from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Category, Comment, Post, Tag

User = get_user_model()


class BaseAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username="author", password="pass12345")
        cls.other = User.objects.create_user(username="other", password="pass12345")
        cls.category = Category.objects.create(name="Web Development")
        cls.tag = Tag.objects.create(name="django")
        cls.post = Post.objects.create(
            title="API Post",
            content="Content via API",
            author=cls.author,
            category=cls.category,
        )
        cls.post.tags.add(cls.tag)

    def authenticate(self, username="author"):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": username, "password": "pass12345"},
        )
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class JWTAuthTests(BaseAPITest):
    def test_obtain_token_pair(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "author", "password": "pass12345"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        pair = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "author", "password": "pass12345"},
        ).data
        response = self.client.post(
            reverse("token_refresh"), {"refresh": pair["refresh"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_credentials_rejected(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "author", "password": "wrong"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostAPITests(BaseAPITest):
    def test_anonymous_can_list_published_posts(self):
        response = self.client.get("/api/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_anonymous_cannot_see_drafts(self):
        Post.objects.create(
            title="Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        response = self.client.get("/api/posts/")
        self.assertEqual(response.data["count"], 1)

    def test_author_sees_own_drafts(self):
        Post.objects.create(
            title="Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        self.authenticate("author")
        response = self.client.get("/api/posts/")
        self.assertEqual(response.data["count"], 2)

    def test_anonymous_cannot_create(self):
        response = self.client.post("/api/posts/", {"title": "X", "content": "Y"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_create_sets_author(self):
        self.authenticate("other")
        response = self.client.post(
            "/api/posts/",
            {
                "title": "Created via API",
                "content": "Body",
                "status": "published",
                "category": self.category.slug,
                "tags": [self.tag.slug],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(title="Created via API")
        self.assertEqual(post.author, self.other)
        self.assertEqual(post.slug, "created-via-api")

    def test_non_author_cannot_update(self):
        self.authenticate("other")
        response = self.client.patch(
            f"/api/posts/{self.post.id}/", {"title": "Hijacked"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_update(self):
        self.authenticate("author")
        response = self.client.patch(
            f"/api/posts/{self.post.id}/", {"title": "Updated Title"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Title")

    def test_non_author_cannot_delete(self):
        self.authenticate("other")
        response = self.client.delete(f"/api/posts/{self.post.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_filter(self):
        Post.objects.create(title="Unrelated", content="nothing", author=self.author)
        response = self.client.get("/api/posts/", {"search": "API"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "API Post")

    def test_filter_by_tag_slug(self):
        Post.objects.create(title="Untagged", content="x", author=self.author)
        response = self.client.get("/api/posts/", {"tags__slug": "django"})
        self.assertEqual(response.data["count"], 1)

    def test_detail_includes_comments_and_likes(self):
        Comment.objects.create(post=self.post, author=self.other, body="hi")
        self.post.likes.add(self.other)
        response = self.client.get(f"/api/posts/{self.post.id}/")
        self.assertEqual(response.data["like_count"], 1)
        self.assertEqual(len(response.data["comments"]), 1)


class PostActionAPITests(BaseAPITest):
    def test_like_toggle(self):
        self.authenticate("other")
        url = f"/api/posts/{self.post.id}/like/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["like_count"], 1)
        self.assertTrue(response.data["is_liked"])
        response = self.client.post(url)
        self.assertEqual(response.data["like_count"], 0)
        self.assertFalse(response.data["is_liked"])

    def test_like_requires_auth(self):
        response = self.client.post(f"/api/posts/{self.post.id}/like/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_comment(self):
        self.authenticate("other")
        response = self.client.post(
            f"/api/posts/{self.post.id}/comments/", {"body": "API comment"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.body, "API comment")
        self.assertEqual(comment.author, self.other)


class CommentAPITests(BaseAPITest):
    def setUp(self):
        self.comment = Comment.objects.create(
            post=self.post, author=self.other, body="A comment"
        )

    def test_list_comments_filtered_by_post(self):
        response = self.client.get("/api/comments/", {"post": self.post.id})
        self.assertEqual(response.data["count"], 1)

    def test_author_can_delete_own_comment(self):
        self.authenticate("other")
        response = self.client.delete(f"/api/comments/{self.comment.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_author_cannot_delete_comment(self):
        self.authenticate("author")
        response = self.client.delete(f"/api/comments/{self.comment.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TaxonomyAPITests(BaseAPITest):
    def test_categories_listed_with_post_count(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["post_count"], 1)

    def test_tags_are_read_only(self):
        self.authenticate("author")
        response = self.client.post("/api/tags/", {"name": "newtag"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SchemaTests(APITestCase):
    def test_openapi_schema_served(self):
        response = self.client.get(reverse("api-schema"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_served(self):
        response = self.client.get(reverse("api-docs"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
