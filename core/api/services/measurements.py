from core.api.services import dashboard_models, db


STRATIFICATION_COLUMNS = {
    "none": [],
    "age": ["age_group"],
    "sex": ["gender"],
    "age_sex": ["age_group", "gender"],
}


def list_numeric(
    query=None,
    concept_id=None,
    event_type=None,
    stratification="none",
    limit=100,
    offset=0,
):
    model = dashboard_models.NUMERIC_MEASUREMENT_MODELS[stratification]
    metric_columns = [
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
    ]
    return _list_measurements(
        model,
        metric_columns,
        query=query,
        concept_id=concept_id,
        event_type=event_type,
        stratification=stratification,
        limit=limit,
        offset=offset,
    )


def list_categorical(
    query=None,
    concept_id=None,
    event_type=None,
    stratification="none",
    limit=100,
    offset=0,
):
    model = dashboard_models.CATEGORICAL_MEASUREMENT_MODELS[stratification]
    metric_columns = [
        "value_as_concept_id",
        "value_concept_name",
        "record_count",
        "patient_count",
        "patient_pct",
    ]
    if stratification != "none":
        metric_columns = [
            "value_as_concept_id",
            "value_concept_name",
            "record_count",
            "patient_count",
            "patient_pct_group",
            "patient_pct_concept",
        ]
    return _list_measurements(
        model,
        metric_columns,
        query=query,
        concept_id=concept_id,
        event_type=event_type,
        stratification=stratification,
        limit=limit,
        offset=offset,
    )


def _list_measurements(
    model,
    metric_columns,
    query=None,
    concept_id=None,
    event_type=None,
    stratification="none",
    limit=100,
    offset=0,
):
    queryset = model.objects.all()
    if query:
        queryset = queryset.filter(concept_name__icontains=query)
    if concept_id:
        queryset = queryset.filter(concept_id=concept_id)
    if event_type:
        queryset = queryset.filter(event_type=event_type)

    columns = [
        "concept_id",
        "concept_name",
        "vocabulary_id",
        "concept_code",
        "event_type",
        *STRATIFICATION_COLUMNS[stratification],
        *metric_columns,
    ]
    order_columns = ["concept_name", "event_type", *STRATIFICATION_COLUMNS[stratification]]

    return db.rows(
        queryset.values(*columns).order_by(*order_columns)[offset : offset + limit]
    )
