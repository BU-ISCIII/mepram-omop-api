from core.api.services import db


CAPABILITIES = {
    "supports_clinical_aggregates": True,
    "supports_age_stratification": True,
    "supports_sex_stratification": True,
    "supports_numeric_measurements": True,
    "supports_categorical_measurements": True,
    "supports_isolate_explorer": False,
    "supports_genomic_alerts": False,
}


def metadata_summary():
    event_types = db.fetch_all(
        "SELECT DISTINCT event_type FROM %s ORDER BY event_type"
        % db.dashboard_table("fact_concept")
    )
    domains = db.fetch_all(
        """
        SELECT domain_id, medical_concepts, participants
        FROM %s
        ORDER BY participants DESC, domain_id
        """
        % db.dashboard_table("fact_domain")
    )
    age_groups = db.fetch_all(
        "SELECT DISTINCT age_group FROM %s WHERE age_group IS NOT NULL ORDER BY age_group"
        % db.dashboard_table("dim_patient")
    )
    genders = db.fetch_all(
        "SELECT DISTINCT gender FROM %s WHERE gender IS NOT NULL ORDER BY gender"
        % db.dashboard_table("dim_patient")
    )
    vocabularies = db.fetch_all(
        """
        SELECT DISTINCT vocabulary_id
        FROM %s
        WHERE vocabulary_id IS NOT NULL
        ORDER BY vocabulary_id
        """
        % db.dashboard_table("concepts")
    )
    total = db.fetch_one(
        "SELECT COUNT(*) AS total_patients FROM %s" % db.dashboard_table("dim_patient")
    )
    return {
        "schema": db.dashboard_schema(),
        "domains": domains,
        "event_types": [row["event_type"] for row in event_types],
        "age_groups": [row["age_group"] for row in age_groups],
        "genders": [row["gender"] for row in genders],
        "vocabularies": [row["vocabulary_id"] for row in vocabularies],
        "total_patients": int(total["total_patients"]),
        "capabilities": capabilities(),
    }


def capabilities():
    return dict(CAPABILITIES)
