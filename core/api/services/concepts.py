from core.api.services import db


def list_concepts(
    query=None,
    domain_id=None,
    vocabulary_id=None,
    limit=100,
    offset=0,
):
    clauses = []
    params = []
    if query:
        clauses.append("concept_name ILIKE %s")
        params.append("%%%s%%" % query)
    if domain_id:
        clauses.append("domain_id = %s")
        params.append(domain_id)
    if vocabulary_id:
        clauses.append("vocabulary_id = %s")
        params.append(vocabulary_id)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.extend([limit, offset])

    return db.fetch_all(
        """
        SELECT concept_id, concept_name, domain_id, vocabulary_id, concept_code
        FROM {concepts}
        {where}
        ORDER BY concept_name, concept_id
        LIMIT %s OFFSET %s
        """.format(concepts=db.dashboard_table("concepts"), where=where),
        params,
    )


def get_concept(concept_id):
    return db.fetch_one(
        """
        SELECT concept_id, concept_name, domain_id, vocabulary_id, concept_code
        FROM {concepts}
        WHERE concept_id = %s
        """.format(concepts=db.dashboard_table("concepts")),
        [concept_id],
    )


def concept_detail(concept_id, event_type=None):
    concept = get_concept(concept_id)
    if concept is None:
        return None

    where_event = "AND event_type = %s" if event_type else ""
    params = [concept_id]
    if event_type:
        params.append(event_type)

    return {
        "concept": concept,
        "summary": db.fetch_all(
            """
            SELECT event_type, record_count, record_pct_overall, patient_count, patient_pct
            FROM {fact_concept}
            WHERE concept_id = %s {where_event}
            ORDER BY event_type
            """.format(
                fact_concept=db.dashboard_table("fact_concept"),
                where_event=where_event,
            ),
            params,
        ),
        "by_age": db.fetch_all(
            """
            SELECT event_type, age_group, patient_count, patient_pct_group, patient_pct_concept
            FROM {fact_concept_by_age}
            WHERE concept_id = %s {where_event}
            ORDER BY event_type, age_group
            """.format(
                fact_concept_by_age=db.dashboard_table("fact_concept_by_age"),
                where_event=where_event,
            ),
            params,
        ),
        "by_sex": db.fetch_all(
            """
            SELECT event_type, gender, patient_count, patient_pct_group, patient_pct_concept
            FROM {fact_concept_by_sex}
            WHERE concept_id = %s {where_event}
            ORDER BY event_type, gender
            """.format(
                fact_concept_by_sex=db.dashboard_table("fact_concept_by_sex"),
                where_event=where_event,
            ),
            params,
        ),
        "by_age_sex": db.fetch_all(
            """
            SELECT event_type, age_group, gender, patient_count, patient_pct_group, patient_pct_concept
            FROM {fact_concept_by_age_sex}
            WHERE concept_id = %s {where_event}
            ORDER BY event_type, age_group, gender
            """.format(
                fact_concept_by_age_sex=db.dashboard_table("fact_concept_by_age_sex"),
                where_event=where_event,
            ),
            params,
        ),
        "measurements": {
            "numeric": db.fetch_all(
                """
                SELECT event_type, unit_concept_id, unit_name, n_records, n_patients,
                       mean_value, sd_value, min_value, q1_value, median_value,
                       q3_value, max_value
                FROM {fact_measurement_numeric}
                WHERE concept_id = %s {where_event}
                ORDER BY event_type, unit_name, unit_concept_id
                """.format(
                    fact_measurement_numeric=db.dashboard_table(
                        "fact_measurement_numeric"
                    ),
                    where_event=where_event,
                ),
                params,
            ),
            "categorical": db.fetch_all(
                """
                SELECT event_type, value_as_concept_id, value_concept_name,
                       record_count, patient_count, patient_pct
                FROM {fact_measurement_categorical}
                WHERE concept_id = %s {where_event}
                ORDER BY event_type, value_concept_name, value_as_concept_id
                """.format(
                    fact_measurement_categorical=db.dashboard_table(
                        "fact_measurement_categorical"
                    ),
                    where_event=where_event,
                ),
                params,
            ),
        },
    }
