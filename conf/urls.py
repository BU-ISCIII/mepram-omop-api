from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="v1/", permanent=False)),
    # Stable, unauthenticated deployment readiness endpoint used by Compose,
    # Apache diagnostics, and the standard smoke-test dispatcher.
    path("health/", include("deployment_health.urls")),
    path("admin/", admin.site.urls),
    path("swagger/", RedirectView.as_view(url="/v1/swagger/", permanent=False)),
    path("v1/", include("core.api.v1.urls", namespace="v1")),
]
