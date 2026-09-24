"""Root URL configuration with the standard deployment health endpoint."""

from django.urls import include, path

# BEGIN BU-ISCIII APPLICATION: django-url-imports
from django.contrib import admin
from django.views.generic import RedirectView
# END BU-ISCIII APPLICATION: django-url-imports

urlpatterns = [
    # Required by Compose health checks and deployment smoke tests.
    path("health/", include("deployment_health.urls")),
    # BEGIN BU-ISCIII APPLICATION: django-url-routes
    path("", RedirectView.as_view(url="v1/", permanent=False)),
    path("admin/", admin.site.urls),
    path("swagger/", RedirectView.as_view(url="/v1/swagger/", permanent=False)),
    path("v1/", include("core.api.v1.urls", namespace="v1")),
    # END BU-ISCIII APPLICATION: django-url-routes
]
