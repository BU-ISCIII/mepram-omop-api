from core.api.services import dashboard_models, db


STRATIFICATION_COLUMNS = {
    "none": [],
    "age": ["age_group"],
    "sex": ["gender"],
    "age_sex": ["age_group", "gender"],
}

FACT_COLUMNS = {
    "none": ["record_count", "record_pct_overall", "patient_count", "patient_pct"],
    "age": ["patient_count", "patient_pct_group", "patient_pct_concept"],
    "sex": ["patient_count", "patient_pct_group", "patient_pct_concept"],
    "age_sex": ["patient_count", "patient_pct_group", "patient_pct_concept"],
}


def list_concepts(
    query=None,
    domain_id=None,
    event_type=None,
    stratification="none",
    limit=100,
    offset=0,
):
    model = dashboard_models.FACT_CONCEPT_MODELS[stratification]
    queryset = model.objects.all()
    if query:
        queryset = queryset.filter(concept_name__icontains=query)
    if domain_id:
        queryset = queryset.filter(domain_id=domain_id)
    if event_type:
        queryset = queryset.filter(event_type=event_type)

    columns = [
        "concept_id",
        "concept_name",
        "domain_id",
        "vocabulary_id",
        "concept_code",
        "event_type",
        *STRATIFICATION_COLUMNS[stratification],
        *FACT_COLUMNS[stratification],
    ]
    order_columns = [
        "-patient_count",
        "concept_name",
        "event_type",
        *STRATIFICATION_COLUMNS[stratification],
    ]

    return db.rows(
        queryset.values(*columns).order_by(*order_columns)[offset : offset + limit]
    )
