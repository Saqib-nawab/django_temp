from django.urls import path

from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("new/", views.post_create, name="post_create"),
    path("mine/", views.my_posts, name="my_posts"),
    path("<int:post_id>/", views.post_detail, name="post_detail"),
    path("<int:post_id>/edit/", views.post_update, name="post_update"),
    path("<int:post_id>/delete/", views.post_delete, name="post_delete"),
    path("<int:post_id>/like/", views.post_like, name="post_like"),
    path("<int:post_id>/comment/", views.comment_create, name="comment_create"),
]
