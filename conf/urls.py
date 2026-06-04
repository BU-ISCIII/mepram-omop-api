from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url="v1/", permanent=False)),
    path("swagger/", RedirectView.as_view(url="/v1/swagger/", permanent=False)),
    path("v1/", include("core.api.v1.urls", namespace="v1")),
]
