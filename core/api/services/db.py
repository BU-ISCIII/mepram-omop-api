from django.conf import settings
from django.db import connection
from decimal import Decimal

DASHBOARD_TABLES = [
    "dim_patient",
    "concepts",
    "events_long",
    "fact_domain",
    "fact_concept",
    "fact_concept_by_age",
    "fact_concept_by_sex",
    "fact_concept_by_age_sex",
    "fact_measurement_numeric",
    "fact_measurement_numeric_by_age",
    "fact_measurement_numeric_by_sex",
    "fact_measurement_numeric_by_age_sex",
    "fact_measurement_categorical",
    "fact_measurement_categorical_by_age",
    "fact_measurement_categorical_by_sex",
    "fact_measurement_categorical_by_age_sex",
]

FACT_CONCEPT_TABLES = {
    "none": "fact_concept",
    "age": "fact_concept_by_age",
    "sex": "fact_concept_by_sex",
    "age_sex": "fact_concept_by_age_sex",
}
NUMERIC_MEASUREMENT_TABLES = {
    "none": "fact_measurement_numeric",
    "age": "fact_measurement_numeric_by_age",
    "sex": "fact_measurement_numeric_by_sex",
    "age_sex": "fact_measurement_numeric_by_age_sex",
}
CATEGORICAL_MEASUREMENT_TABLES = {
    "none": "fact_measurement_categorical",
    "age": "fact_measurement_categorical_by_age",
    "sex": "fact_measurement_categorical_by_sex",
    "age_sex": "fact_measurement_categorical_by_age_sex",
}

VALID_STRATIFICATIONS = set(FACT_CONCEPT_TABLES)


def dashboard_schema():
    return settings.MEPRAM_DASHBOARD_SCHEMA


def dashboard_table(table_name):
    if table_name not in DASHBOARD_TABLES:
        raise ValueError("Unknown dashboard table: %s" % table_name)
    return '"%s"."%s"' % (dashboard_schema().replace('"', '""'), table_name)


def fetch_all(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [column[0] for column in cursor.description]
        return [
            {key: _json_value(value) for key, value in zip(columns, row)}
            for row in cursor.fetchall()
        ]


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def _json_value(value):
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value
