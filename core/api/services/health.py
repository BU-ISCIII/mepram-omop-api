from django.db import DatabaseError, connection
from django.utils import timezone

from core.api.services import db


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
                {"table": table, "exists": None, "row_count": None}
                for table in db.DASHBOARD_TABLES
            ],
            "checked_at": checked_at,
        }

    present_rows = db.fetch_all(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        """,
        [db.dashboard_schema()],
    )
    present = {row["table_name"] for row in present_rows}
    tables = []
    for table in db.DASHBOARD_TABLES:
        if table not in present:
            tables.append({"table": table, "exists": False, "row_count": None})
            continue
        count_row = db.fetch_one(
            "SELECT COUNT(*) AS row_count FROM %s" % db.dashboard_table(table)
        )
        tables.append(
            {
                "table": table,
                "exists": True,
                "row_count": int(count_row["row_count"]),
            }
        )

    status = "UP" if all(item["exists"] for item in tables) else "DEGRADED"
    return {
        "status": status,
        "schema": db.dashboard_schema(),
        "tables": tables,
        "checked_at": checked_at,
    }
