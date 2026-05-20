from core.api.services import db


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
    table = db.FACT_CONCEPT_TABLES[stratification]
    clauses = []
    params = []
    if query:
        clauses.append("concept_name ILIKE %s")
        params.append("%%%s%%" % query)
    if domain_id:
        clauses.append("domain_id = %s")
        params.append(domain_id)
    if event_type:
        clauses.append("event_type = %s")
        params.append(event_type)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
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
        "patient_count DESC",
        "concept_name",
        "event_type",
        *STRATIFICATION_COLUMNS[stratification],
    ]
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
