from django.conf import settings
from decimal import Decimal


def dashboard_schema():
    return settings.MEPRAM_DASHBOARD_SCHEMA


def rows(queryset):
    return [{key: _json_value(value) for key, value in row.items()} for row in queryset]


def row(queryset):
    items = rows(queryset[:1])
    return items[0] if items else None


def _json_value(value):
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value
