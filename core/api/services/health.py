from django.db import DatabaseError, connection
from django.utils import timezone

from core.api.services import dashboard_models, db


def health_check():
    checked_at = timezone.now().isoformat()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return {
            "status": "DOWN",
            "schema": db.dashboard_schema(),
            "tables": [
                {"table": model._meta.db_table, "exists": None, "row_count": None}
                for model in dashboard_models.DASHBOARD_MODELS
            ],
            "checked_at": checked_at,
        }

    present = set(connection.introspection.table_names())
    tables = []
    for model in dashboard_models.DASHBOARD_MODELS:
        table = model._meta.db_table
        if table not in present:
            tables.append({"table": table, "exists": False, "row_count": None})
            continue
        tables.append(
            {
                "table": table,
                "exists": True,
                "row_count": model.objects.count(),
            }
        )

    status = "UP" if all(item["exists"] for item in tables) else "DEGRADED"
    return {
        "status": status,
        "schema": db.dashboard_schema(),
        "tables": tables,
        "checked_at": checked_at,
    }
