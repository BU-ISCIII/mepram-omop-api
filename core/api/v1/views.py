from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.api.services import cohort, concepts, domains, facts, health, measurements, metadata
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
    responses={200: serializers.HealthResponseSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_view(request):
    return Response(health.health_check(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Dashboard metadata",
    responses={200: serializers.MetadataResponseSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def metadata_view(request):
    return Response(metadata.metadata_summary(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Dashboard capabilities",
    responses={200: dict},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def capabilities_view(request):
    return Response(metadata.capabilities(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="Cohort summary",
    responses={200: dict},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def cohort_summary_view(request):
    return Response(cohort.summary(), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="List dashboard domains",
    parameters=[OpenApiParameter("q", str, required=False)],
    responses={200: serializers.DomainSerializer(many=True)},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def domains_view(request):
    params = _validated(serializers.DomainQuerySerializer, request.query_params)
    return Response(domains.list_domains(params.get("q")), status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_DASHBOARD],
    summary="List concepts for one domain",
    parameters=[
        OpenApiParameter("q", str, required=False),
        OpenApiParameter("limit", int, required=False),
        OpenApiParameter("offset", int, required=False),
    ],
    responses={200: serializers.DomainConceptResponseSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
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
@authentication_classes([])
@permission_classes([AllowAny])
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
    responses={200: serializers.ConceptSerializer, 404: serializers.ErrorSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def concept_detail_view(request, concept_id):
    row = concepts.get_concept(concept_id)
    if row is None:
        return Response({"error": "Concept not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(row, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CONCEPTS],
    summary="Get concept dashboard detail",
    parameters=[OpenApiParameter("event_type", str, required=False)],
    responses={200: dict, 404: serializers.ErrorSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
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
    parameters=FACT_CONCEPT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
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
    parameters=MEASUREMENT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
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
    parameters=MEASUREMENT_PARAMETERS,
    responses={200: dict},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
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
