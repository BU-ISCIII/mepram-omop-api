from core.api.services import db


def summary():
    return {
        "total_patients": _total_patients(),
        "by_age": db.fetch_all(
            """
            SELECT age_group, COUNT(*)::integer AS patients
            FROM {patients}
            WHERE age_group IS NOT NULL
            GROUP BY age_group
            ORDER BY age_group
            """.format(patients=db.dashboard_table("dim_patient"))
        ),
        "by_sex": db.fetch_all(
            """
            SELECT gender, COUNT(*)::integer AS patients
            FROM {patients}
            WHERE gender IS NOT NULL
            GROUP BY gender
            ORDER BY gender
            """.format(patients=db.dashboard_table("dim_patient"))
        ),
        "by_age_sex": db.fetch_all(
            """
            SELECT age_group, gender, COUNT(*)::integer AS patients
            FROM {patients}
            WHERE age_group IS NOT NULL AND gender IS NOT NULL
            GROUP BY age_group, gender
            ORDER BY age_group, gender
            """.format(patients=db.dashboard_table("dim_patient"))
        ),
    }


def _total_patients():
    row = db.fetch_one(
        "SELECT COUNT(*)::integer AS total_patients FROM %s"
        % db.dashboard_table("dim_patient")
    )
    return row["total_patients"]
