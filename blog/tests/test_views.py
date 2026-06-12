from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from blog.models import Category, Comment, Post, Tag
from blog.views import POSTS_PER_PAGE

User = get_user_model()


class BaseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username="author", password="pass12345")
        cls.other = User.objects.create_user(username="other", password="pass12345")
        cls.post = Post.objects.create(
            title="A Published Post", content="Hello content", author=cls.author
        )


class PostListViewTests(BaseViewTest):
    def test_list_shows_published_posts(self):
        response = self.client.get(reverse("post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A Published Post")

    def test_drafts_are_hidden_from_list(self):
        Post.objects.create(
            title="Secret Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        response = self.client.get(reverse("post_list"))
        self.assertNotContains(response, "Secret Draft")

    def test_search_matches_title(self):
        Post.objects.create(title="Django Tips", content="x", author=self.author)
        response = self.client.get(reverse("post_list"), {"q": "django"})
        self.assertContains(response, "Django Tips")
        self.assertNotContains(response, "A Published Post")

    def test_search_matches_tag_name(self):
        tagged = Post.objects.create(title="Tagged Post", content="x", author=self.author)
        tagged.tags.add(Tag.objects.create(name="postgresql"))
        response = self.client.get(reverse("post_list"), {"q": "postgresql"})
        self.assertContains(response, "Tagged Post")

    def test_filter_by_tag(self):
        tag = Tag.objects.create(name="docker")
        tagged = Post.objects.create(title="Docker Post", content="x", author=self.author)
        tagged.tags.add(tag)
        response = self.client.get(reverse("post_list"), {"tag": tag.slug})
        self.assertContains(response, "Docker Post")
        self.assertNotContains(response, "A Published Post")

    def test_filter_by_category(self):
        category = Category.objects.create(name="DevOps")
        Post.objects.create(
            title="Categorised Post", content="x", author=self.author, category=category
        )
        response = self.client.get(reverse("post_list"), {"category": category.slug})
        self.assertContains(response, "Categorised Post")
        self.assertNotContains(response, "A Published Post")

    def test_pagination(self):
        for i in range(POSTS_PER_PAGE + 1):
            Post.objects.create(title=f"Filler {i}", content="x", author=self.author)
        response = self.client.get(reverse("post_list"))
        self.assertEqual(len(response.context["posts"]), POSTS_PER_PAGE)
        response_page2 = self.client.get(reverse("post_list"), {"page": 2})
        self.assertEqual(response_page2.status_code, 200)


class PostDetailViewTests(BaseViewTest):
    def test_detail_renders(self):
        response = self.client.get(reverse("post_detail", args=[self.post.id]))
        self.assertContains(response, "A Published Post")

    def test_draft_returns_404_for_other_users(self):
        draft = Post.objects.create(
            title="Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        response = self.client.get(reverse("post_detail", args=[draft.id]))
        self.assertEqual(response.status_code, 404)

    def test_draft_visible_to_author(self):
        draft = Post.objects.create(
            title="Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        self.client.login(username="author", password="pass12345")
        response = self.client.get(reverse("post_detail", args=[draft.id]))
        self.assertEqual(response.status_code, 200)


class PostCrudViewTests(BaseViewTest):
    def test_create_requires_login(self):
        response = self.client.get(reverse("post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_create_post(self):
        self.client.login(username="author", password="pass12345")
        response = self.client.post(
            reverse("post_create"),
            {"title": "Fresh Post", "content": "Body", "status": "published"},
        )
        post = Post.objects.get(title="Fresh Post")
        self.assertRedirects(response, reverse("post_detail", args=[post.id]))
        self.assertEqual(post.author, self.author)

    def test_update_forbidden_for_non_author(self):
        self.client.login(username="other", password="pass12345")
        response = self.client.get(reverse("post_update", args=[self.post.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_forbidden_for_non_author(self):
        self.client.login(username="other", password="pass12345")
        response = self.client.post(reverse("post_delete", args=[self.post.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_author_can_delete(self):
        self.client.login(username="author", password="pass12345")
        response = self.client.post(reverse("post_delete", args=[self.post.id]))
        self.assertRedirects(response, reverse("post_list"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class LikeAndCommentViewTests(BaseViewTest):
    def test_like_toggles(self):
        self.client.login(username="other", password="pass12345")
        url = reverse("post_like", args=[self.post.id])
        self.client.post(url)
        self.assertEqual(self.post.likes.count(), 1)
        self.client.post(url)
        self.assertEqual(self.post.likes.count(), 0)

    def test_like_requires_login(self):
        response = self.client.post(reverse("post_like", args=[self.post.id]))
        self.assertEqual(response.status_code, 302)

    def test_comment_created(self):
        self.client.login(username="other", password="pass12345")
        self.client.post(
            reverse("comment_create", args=[self.post.id]), {"body": "Nice post!"}
        )
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.body, "Nice post!")
        self.assertEqual(comment.author, self.other)

    def test_comment_shown_on_detail_page(self):
        Comment.objects.create(post=self.post, author=self.other, body="Visible comment")
        response = self.client.get(reverse("post_detail", args=[self.post.id]))
        self.assertContains(response, "Visible comment")


class MyPostsViewTests(BaseViewTest):
    def test_requires_login(self):
        response = self.client.get(reverse("my_posts"))
        self.assertEqual(response.status_code, 302)

    def test_shows_own_posts_including_drafts(self):
        Post.objects.create(
            title="My Draft", content="x", author=self.author, status=Post.Status.DRAFT
        )
        self.client.login(username="author", password="pass12345")
        response = self.client.get(reverse("my_posts"))
        self.assertContains(response, "My Draft")
        self.assertContains(response, "A Published Post")

    def test_does_not_show_other_users_posts(self):
        Post.objects.create(title="Not Mine", content="x", author=self.other)
        self.client.login(username="author", password="pass12345")
        response = self.client.get(reverse("my_posts"))
        self.assertNotContains(response, "Not Mine")


class SignupViewTests(TestCase):
    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newbie",
                "password1": "a-strong-pass-123",
                "password2": "a-strong-pass-123",
            },
        )
        self.assertRedirects(response, reverse("post_list"))
        self.assertTrue(User.objects.filter(username="newbie").exists())
