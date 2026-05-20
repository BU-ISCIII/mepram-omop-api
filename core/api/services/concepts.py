from core import models
from core.api.services import db


def list_concepts(
    query=None,
    domain_id=None,
    vocabulary_id=None,
    limit=100,
    offset=0,
):
    queryset = models.Concept.objects.all()
    if query:
        queryset = queryset.filter(concept_name__icontains=query)
    if domain_id:
        queryset = queryset.filter(domain_id=domain_id)
    if vocabulary_id:
        queryset = queryset.filter(vocabulary_id=vocabulary_id)

    return db.rows(
        queryset.values(
            "concept_id", "concept_name", "domain_id", "vocabulary_id", "concept_code"
        ).order_by("concept_name", "concept_id")[offset : offset + limit]
    )


def get_concept(concept_id):
    return db.row(
        models.Concept.objects.filter(concept_id=concept_id).values(
            "concept_id", "concept_name", "domain_id", "vocabulary_id", "concept_code"
        )
    )


def concept_detail(concept_id, event_type=None):
    concept = get_concept(concept_id)
    if concept is None:
        return None

    fact_filter = {"concept_id": concept_id}
    if event_type:
        fact_filter["event_type"] = event_type

    return {
        "concept": concept,
        "summary": db.rows(
            models.FactConcept.objects.filter(**fact_filter)
            .values(
                "event_type",
                "record_count",
                "record_pct_overall",
                "patient_count",
                "patient_pct",
            )
            .order_by("event_type")
        ),
        "by_age": db.rows(
            models.FactConceptByAge.objects.filter(**fact_filter)
            .values(
                "event_type",
                "age_group",
                "patient_count",
                "patient_pct_group",
                "patient_pct_concept",
            )
            .order_by("event_type", "age_group")
        ),
        "by_sex": db.rows(
            models.FactConceptBySex.objects.filter(**fact_filter)
            .values(
                "event_type",
                "gender",
                "patient_count",
                "patient_pct_group",
                "patient_pct_concept",
            )
            .order_by("event_type", "gender")
        ),
        "by_age_sex": db.rows(
            models.FactConceptByAgeSex.objects.filter(**fact_filter)
            .values(
                "event_type",
                "age_group",
                "gender",
                "patient_count",
                "patient_pct_group",
                "patient_pct_concept",
            )
            .order_by("event_type", "age_group", "gender")
        ),
        "measurements": {
            "numeric": db.rows(
                models.FactMeasurementNumeric.objects.filter(**fact_filter)
                .values(
                    "event_type",
                    "unit_concept_id",
                    "unit_name",
                    "n_records",
                    "n_patients",
                    "mean_value",
                    "sd_value",
                    "min_value",
                    "q1_value",
                    "median_value",
                    "q3_value",
                    "max_value",
                )
                .order_by("event_type", "unit_name", "unit_concept_id")
            ),
            "categorical": db.rows(
                models.FactMeasurementCategorical.objects.filter(**fact_filter)
                .values(
                    "event_type",
                    "value_as_concept_id",
                    "value_concept_name",
                    "record_count",
                    "patient_count",
                    "patient_pct",
                )
                .order_by("event_type", "value_concept_name", "value_as_concept_id")
            ),
        },
    }
