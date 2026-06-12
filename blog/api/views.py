from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from blog.models import Category, Comment, Post, Tag

from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
    TagSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(post_count=Count("posts")).order_by("name")
    serializer_class = CategorySerializer
    lookup_field = "slug"


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.annotate(post_count=Count("posts")).order_by("name")
    serializer_class = TagSerializer
    lookup_field = "slug"


class PostViewSet(viewsets.ModelViewSet):
    """
    CRUD for blog posts.

    Anonymous users see published posts only; authenticated users also see
    their own drafts. Only the author may update or delete a post.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "category__slug": ["exact"],
        "tags__slug": ["exact"],
        "status": ["exact"],
        "author__username": ["exact"],
    }
    search_fields = ["title", "content", "tags__name"]
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category").prefetch_related(
            "tags", "comments__author", "likes"
        )
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=user)
            ).distinct()
        return queryset.filter(status=Post.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(request=None, responses={200: PostDetailSerializer})
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Toggle a like on a post for the current user."""
        post = self.get_object()
        if post.likes.filter(pk=request.user.pk).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
        serializer = PostDetailSerializer(post, context={"request": request})
        return Response(serializer.data)

    @extend_schema(request=CommentSerializer, responses={201: CommentSerializer})
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="comments",
    )
    def add_comment(self, request, pk=None):
        """Add a comment to a post."""
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(
    viewsets.mixins.RetrieveModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Read, update, and delete comments. Only the comment author may modify."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["post"]

    def get_queryset(self):
        return Comment.objects.filter(active=True).select_related("author", "post")
