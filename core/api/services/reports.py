from django.db.models import Count
from django.utils import timezone

from core import models
from core.api.services import db

from jsonschema import validate, ValidationError
import json

def _validate_payload(payload):
    # Placeholder for payload validation logic
    with open("core/api/services/report_payload_schema.json") as schema_file:
        json_schema = json.load(schema_file)
    validate(instance=payload, schema=json_schema)

def report(params=None):
    all_models = models.ReportCache.objects.all()
    if params:
        start = params.get("start_date")
        end = params.get("end_date")
        all_models = all_models.filter(created_at__gte=start, created_at__lte=end)
        if params.get("summary_name"):
            all_models = all_models.filter(summary_name__iexact=params.get("summary_name"))
        all_models = all_models.order_by("-created_at")[: params.get("limit", 20)]

    # Return everything except the primary key
    fields = [
        f.name
        for f in models.ReportCache._meta.concrete_fields
        if not f.primary_key
    ]
    return all_models.values(*fields)

def save_report(validated_data):
    _validate_payload(validated_data["payload"])  # Validate the payload before saving
    # Create a new ReportCache instance with the validated data
    report_cache = models.ReportCache(**validated_data)
    report_cache.created_at = timezone.now()
    report_cache.updated_at = timezone.now()
    report_cache.save()
