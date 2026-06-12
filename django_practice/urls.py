"""URL configuration for django_practice project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from blog import views as blog_views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="post_list", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/signup/", blog_views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("blog/", include("blog.urls")),
    path("api/", include("blog.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
