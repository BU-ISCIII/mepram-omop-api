from core.api.services import db


def list_domains(query=None):
    if not query:
        return db.fetch_all(
            """
            SELECT domain_id, medical_concepts, participants
            FROM %s
            ORDER BY participants DESC, domain_id
            """
            % db.dashboard_table("fact_domain")
        )

    return db.fetch_all(
        """
        SELECT e.domain_id,
               COUNT(DISTINCT e.concept_id)::integer AS medical_concepts,
               COUNT(DISTINCT e.person_id)::integer AS participants
        FROM {events} e
        JOIN {concepts} c ON c.concept_id = e.concept_id
        WHERE c.concept_name ILIKE %s
        GROUP BY e.domain_id
        ORDER BY participants DESC, e.domain_id
        """.format(
            events=db.dashboard_table("events_long"),
            concepts=db.dashboard_table("concepts"),
        ),
        ["%%%s%%" % query],
    )


def domain_concepts(domain_id, query=None, limit=100, offset=0):
    params = [domain_id]
    name_filter = ""
    if query:
        name_filter = "AND c.concept_name ILIKE %s"
        params.append("%%%s%%" % query)
    params.extend([limit, offset])

    rows = db.fetch_all(
        """
        WITH cohort AS (
            SELECT COUNT(*)::double precision AS n FROM {patients}
        )
        SELECT c.concept_id,
               c.concept_name,
               c.vocabulary_id,
               c.concept_code,
               COUNT(DISTINCT e.person_id)::integer AS participants,
               COUNT(DISTINCT e.person_id) / NULLIF((SELECT n FROM cohort), 0) * 100.0 AS pct
        FROM {events} e
        JOIN {concepts} c ON c.concept_id = e.concept_id
        WHERE e.domain_id = %s
          {name_filter}
        GROUP BY c.concept_id, c.concept_name, c.vocabulary_id, c.concept_code
        ORDER BY participants DESC, c.concept_name
        LIMIT %s OFFSET %s
        """.format(
            patients=db.dashboard_table("dim_patient"),
            events=db.dashboard_table("events_long"),
            concepts=db.dashboard_table("concepts"),
            name_filter=name_filter,
        ),
        params,
    )
    total = db.fetch_one(
        """
        SELECT COUNT(DISTINCT e.person_id)::integer AS total_participants
        FROM {events} e
        JOIN {concepts} c ON c.concept_id = e.concept_id
        WHERE e.domain_id = %s
          {name_filter}
        """.format(
            events=db.dashboard_table("events_long"),
            concepts=db.dashboard_table("concepts"),
            name_filter=name_filter,
        ),
        params[:-2],
    )
    return {"total_participants": total["total_participants"], "data": rows}
