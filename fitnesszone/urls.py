from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
import os

from shop import views as shop_views

admin.site.site_header = f"{settings.SITE_NAME} administration"
admin.site.site_title = f"{settings.SITE_NAME} admin"
admin.site.index_title = "Store, catalogue and orders"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("workouts/", include("workouts.urls")),
    path("", shop_views.home, name="home"),
    path("", include("shop.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif os.environ.get("SERVE_MEDIA") == "1":
    # Simple option for small sites: serve uploaded product images from MEDIA_ROOT (use a persistent disk).
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
