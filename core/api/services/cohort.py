from django.db.models import Count

from core import models
from core.api.services import db


def summary():
    return {
        "total_patients": _total_patients(),
        "by_age": db.rows(
            models.DimPatient.objects.exclude(age_group__isnull=True)
            .values("age_group")
            .annotate(patients=Count("person_id"))
            .order_by("age_group")
        ),
        "by_sex": db.rows(
            models.DimPatient.objects.exclude(gender__isnull=True)
            .values("gender")
            .annotate(patients=Count("person_id"))
            .order_by("gender")
        ),
        "by_age_sex": db.rows(
            models.DimPatient.objects.exclude(age_group__isnull=True)
            .exclude(gender__isnull=True)
            .values("age_group", "gender")
            .annotate(patients=Count("person_id"))
            .order_by("age_group", "gender")
        ),
    }


def _total_patients():
    return models.DimPatient.objects.count()
