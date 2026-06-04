from django.urls import path

from core.api.v1 import views
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = "mepram_api"
namespace="v1"

urlpatterns = [
    path("", RedirectView.as_view(url="swagger/", permanent=False)),
    path("openapi/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="v1:schema"),
        name="swagger-ui",
    ),
    path("health", views.health_view, name="health"),
    path("metadata", views.metadata_view, name="metadata"),
    path("capabilities", views.capabilities_view, name="capabilities"),
    path("cohort/summary", views.cohort_summary_view, name="cohort_summary"),
    path("domains", views.domains_view, name="domains"),
    path(
        "domains/<str:domain_id>/concepts",
        views.domain_concepts_view,
        name="domain_concepts",
    ),
    path("concepts", views.concepts_view, name="concepts"),
    path("concepts/<int:concept_id>", views.concept_detail_view, name="concept_detail"),
    path(
        "concepts/<int:concept_id>/detail",
        views.concept_dashboard_detail_view,
        name="concept_dashboard_detail",
    ),
    path("facts/concepts", views.fact_concepts_view, name="fact_concepts"),
    path(
        "measurements/numeric",
        views.numeric_measurements_view,
        name="numeric_measurements",
    ),
    path(
        "measurements/categorical",
        views.categorical_measurements_view,
        name="categorical_measurements",
    ),
]
