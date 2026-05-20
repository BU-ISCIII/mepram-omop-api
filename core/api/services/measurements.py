from core.api.services import db


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
    table = db.NUMERIC_MEASUREMENT_TABLES[stratification]
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
        table,
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
    table = db.CATEGORICAL_MEASUREMENT_TABLES[stratification]
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
        table,
        metric_columns,
        query=query,
        concept_id=concept_id,
        event_type=event_type,
        stratification=stratification,
        limit=limit,
        offset=offset,
    )


def _list_measurements(
    table,
    metric_columns,
    query=None,
    concept_id=None,
    event_type=None,
    stratification="none",
    limit=100,
    offset=0,
):
    clauses = []
    params = []
    if query:
        clauses.append("concept_name ILIKE %s")
        params.append("%%%s%%" % query)
    if concept_id:
        clauses.append("concept_id = %s")
        params.append(concept_id)
    if event_type:
        clauses.append("event_type = %s")
        params.append(event_type)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
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
    params.extend([limit, offset])

    return db.fetch_all(
        """
        SELECT {columns}
        FROM {table}
        {where}
        ORDER BY {order_columns}
        LIMIT %s OFFSET %s
        """.format(
            columns=", ".join(columns),
            table=db.dashboard_table(table),
            where=where,
            order_columns=", ".join(order_columns),
        ),
        params,
    )
