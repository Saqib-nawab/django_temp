from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Category, Post, Tag

POSTS_PER_PAGE = 6


def post_list(request):
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .prefetch_related("tags")
        .annotate(num_likes=Count("likes", distinct=True), num_comments=Count("comments", distinct=True))
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()

    tag_slug = request.GET.get("tag")
    active_tag = None
    if tag_slug:
        active_tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=active_tag)

    category_slug = request.GET.get("category")
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=active_category)

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "posts": page_obj.object_list,
        "query": query,
        "active_tag": active_tag,
        "active_category": active_category,
        "categories": Category.objects.annotate(num_posts=Count("posts")),
        "tags": Tag.objects.annotate(num_posts=Count("posts")),
    }
    return render(request, "blog/post_list.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "category").prefetch_related(
            "tags", "comments__author"
        ),
        id=post_id,
    )
    if post.status == Post.Status.DRAFT and post.author != request.user:
        raise Http404

    comments = post.comments.filter(active=True)
    comment_form = CommentForm()
    user_has_liked = (
        request.user.is_authenticated and post.likes.filter(pk=request.user.pk).exists()
    )
    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
        "user_has_liked": user_has_liked,
    }
    return render(request, "blog/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            return redirect("post_detail", post_id=post.id)
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})


@login_required
def post_update(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        raise PermissionDenied
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect("post_detail", post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_form.html", {"form": form, "post": post})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        raise PermissionDenied
    if request.method == "POST":
        post.delete()
        return redirect("post_list")
    return render(request, "blog/post_confirm_delete.html", {"post": post})


@login_required
@require_POST
def post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if post.likes.filter(pk=request.user.pk).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect("post_detail", post_id=post.id)


@login_required
@require_POST
def comment_create(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect("post_detail", post_id=post.id)


@login_required
def my_posts(request):
    posts = (
        Post.objects.filter(author=request.user)
        .select_related("category")
        .prefetch_related("tags")
        .annotate(num_likes=Count("likes", distinct=True), num_comments=Count("comments", distinct=True))
        .order_by("-created_at")
    )
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "blog/my_posts.html",
        {"page_obj": page_obj, "posts": page_obj.object_list},
    )


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("post_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
