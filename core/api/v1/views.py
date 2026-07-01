from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.api.services import (
    cohort,
    concepts,
    domains,
    facts,
    health,
    measurements,
    metadata,
    reports,
)
from core.api.v1 import serializers

TAG_OPERATION = "Operation"
TAG_DASHBOARD = "Dashboard"
TAG_CONCEPTS = "Concepts"
TAG_FACTS = "Facts"
TAG_MEASUREMENTS = "Measurements"


def _validated(serializer_class, query_params):
    serializer = serializer_class(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@extend_schema(
    tags=[TAG_OPERATION],
    summary="Health check",
    description='Checks database connectivity and reports whether every Django-managed dashboard table exists. The response includes one entry per table with its existence flag and current row count, so it can be used to verify that migrations and the dashboard import completed successfully.',
    responses={200: serializers.HealthResponseSerializer},
    auth=[],
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_view(request):
    return Response(health.health_check(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Dashboard metadata",
    description='Returns global metadata needed to build filters and navigation: loaded schema name, OMOP domains, available event types, age groups, genders, vocabularies, total patient count and capability flags.',
    responses={200: serializers.MetadataResponseSerializer},
)
@api_view(["GET"])
def metadata_view(request):
    return Response(metadata.metadata_summary(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Dashboard capabilities",
    description='Returns boolean feature flags describing the current scope of the API. Clinical aggregates and stratified measurements are supported; isolate explorer and genomic alert workflows are explicitly marked unsupported.',
    responses={200: dict},
)
@api_view(["GET"])
def capabilities_view(request):
    return Response(metadata.capabilities(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Full descriptive report of one or multiple cohort",
    description='Retrieves available reports from the cohorts',
    responses={200: dict},
    parameters=[
        OpenApiParameter("limit", int, required=False, default=20),
        OpenApiParameter("start_date", OpenApiTypes.DATE, required=False, default="1980-01-01", description="Earliest start date of report submission until today, in YYYY-MM-DD format. If used alongside end_date, it will return all the reports in a date range."),
        OpenApiParameter("end_date", OpenApiTypes.DATE, required=False, default="3000-01-01", description="Latest end date of report submission, in YYYY-MM-DD format. If used alongside start_date, it will return all the reports in a date range."),
        OpenApiParameter("summary_name", str, required=False, description="Name of the report.")
    ]
)
@api_view(["GET"])
def full_report_view(request):
    params = _validated(serializers.ReportQuerySerializer, request.query_params)
    return Response(reports.report(params), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Cohort summary",
    description='Returns the dashboard cohort size and patient distributions by age group, by sex and by the combined age+sex stratification. Counts are based on the distinct patient dimension imported from dashboard.sql.',
    responses={200: dict},
)
@api_view(["GET"])
def cohort_summary_view(request):
    return Response(cohort.summary(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="List dashboard domains",
    description='Lists OMOP domains available in the dashboard.',
    responses={200: serializers.DomainSerializer(many=True)},
)
@api_view(["GET"])
def domains_view(request):
    return Response(domains.list_domains(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="List concepts for one domain",
    description='Lists concepts that belong to one OMOP domain, including the number of distinct patients with at least one event for each concept and the percentage over the whole cohort. Supports text search and pagination.',
    parameters=[
        OpenApiParameter("q", str, required=False),
        OpenApiParameter("limit", int, required=False),
        OpenApiParameter("offset", int, required=False),
    ],
    responses={200: serializers.DomainConceptResponseSerializer},
)
@api_view(["GET"])
def domain_concepts_view(request, domain_id):
    params = _validated(serializers.DomainConceptQuerySerializer, request.query_params)
    payload = domains.domain_concepts(
        domain_id,
        query=params.get("q"),
        limit=params["limit"],
        offset=params["offset"],
    )
    payload["domain_id"] = domain_id
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CONCEPTS],
    summary="Search concepts",
    description='Searches the imported OMOP concept catalogue. The response contains concept identifiers, display names, OMOP domain, vocabulary and source concept code. This endpoint does not include event counts.',
    parameters=[
        OpenApiParameter("q", str, required=False),
        OpenApiParameter("domain_id", str, required=False),
        OpenApiParameter("vocabulary_id", str, required=False),
        OpenApiParameter("limit", int, required=False),
        OpenApiParameter("offset", int, required=False),
    ],
    responses={200: serializers.ConceptSerializer(many=True)},
)
@api_view(["GET"])
def concepts_view(request):
    params = _validated(serializers.ConceptQuerySerializer, request.query_params)
    rows = concepts.list_concepts(
        query=params.get("q"),
        domain_id=params.get("domain_id"),
        vocabulary_id=params.get("vocabulary_id"),
        limit=params["limit"],
        offset=params["offset"],
    )
    return Response(rows, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CONCEPTS],
    summary="Get concept",
    description='Returns catalogue metadata for one concept_id. Use the /detail endpoint when aggregate counts, stratifications or measurement values are needed.',
    responses={200: serializers.ConceptSerializer, 404: serializers.ErrorSerializer},
)
@api_view(["GET"])
def concept_detail_view(request, concept_id):
    row = concepts.get_concept(concept_id)
    if row is None:
        return Response({"error": "Concept not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(row, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CONCEPTS],
    summary="Get concept dashboard detail",
    description='Returns a dashboard-oriented detail view for one concept: concept metadata, overall aggregate counts, age/sex stratifications and any numeric or categorical measurement summaries associated with the same concept_id. Optionally restricts all aggregate sections by event_type.',
    parameters=[OpenApiParameter("event_type", str, required=False)],
    responses={200: dict, 404: serializers.ErrorSerializer},
)
@api_view(["GET"])
def concept_dashboard_detail_view(request, concept_id):
    params = _validated(serializers.ConceptDetailQuerySerializer, request.query_params)
    payload = concepts.concept_detail(concept_id, event_type=params.get("event_type"))
    if payload is None:
        return Response({"error": "Concept not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(payload, status=status.HTTP_200_OK)


FACT_CONCEPT_PARAMETERS = [
    OpenApiParameter("q", str, required=False),
    OpenApiParameter("domain_id", str, required=False),
    OpenApiParameter("event_type", str, required=False),
    OpenApiParameter("stratification", str, required=False),
    OpenApiParameter("limit", int, required=False),
    OpenApiParameter("offset", int, required=False),
]


@extend_schema(
    tags=[TAG_FACTS],
    summary="List concept aggregates",
    description='Lists precomputed concept-level aggregates. With stratification=none it returns record counts, patient counts and percentages. With age, sex or age_sex it returns patient counts and percentages within each stratum and within the concept. Supports text, domain, event type and pagination filters.',
    parameters=FACT_CONCEPT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
def fact_concepts_view(request):
    params = _validated(serializers.FactConceptQuerySerializer, request.query_params)
    return Response(
        facts.list_concepts(
            query=params.get("q"),
            domain_id=params.get("domain_id"),
            event_type=params.get("event_type"),
            stratification=params["stratification"],
            limit=params["limit"],
            offset=params["offset"],
        ),
        status=status.HTTP_200_OK,
    )


MEASUREMENT_PARAMETERS = [
    OpenApiParameter("q", str, required=False),
    OpenApiParameter("concept_id", int, required=False),
    OpenApiParameter("event_type", str, required=False),
    OpenApiParameter("stratification", str, required=False),
    OpenApiParameter("limit", int, required=False),
    OpenApiParameter("offset", int, required=False),
]


@extend_schema(
    tags=[TAG_MEASUREMENTS],
    summary="List numeric measurement aggregates",
    description='Lists numeric measurement summaries for measurement-like concepts. Each row contains unit metadata, number of records/patients and descriptive statistics: mean, standard deviation, min, quartiles, median and max. Optional stratification adds age_group and/or gender columns.',
    parameters=MEASUREMENT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
def numeric_measurements_view(request):
    params = _validated(serializers.MeasurementQuerySerializer, request.query_params)
    return Response(
        measurements.list_numeric(
            query=params.get("q"),
            concept_id=params.get("concept_id"),
            event_type=params.get("event_type"),
            stratification=params["stratification"],
            limit=params["limit"],
            offset=params["offset"],
        ),
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=[TAG_MEASUREMENTS],
    summary="List categorical measurement aggregates",
    description='Lists categorical measurement summaries for concepts represented by value_as_concept_id. The response includes category labels, record and patient counts and percentages. Optional stratification adds age_group and/or gender plus stratum-specific percentages.',
    parameters=MEASUREMENT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
def categorical_measurements_view(request):
    params = _validated(serializers.MeasurementQuerySerializer, request.query_params)
    return Response(
        measurements.list_categorical(
            query=params.get("q"),
            concept_id=params.get("concept_id"),
            event_type=params.get("event_type"),
            stratification=params["stratification"],
            limit=params["limit"],
            offset=params["offset"],
        ),
        status=status.HTTP_200_OK,
    )
