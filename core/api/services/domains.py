from django.db.models import Count

from core import models
from core.api.services import db


def list_domains(query=None):
    if not query:
        return db.rows(
            models.FactDomain.objects.values(
                "domain_id", "medical_concepts", "participants"
            ).order_by("-participants", "domain_id")
        )

    matching_concepts = models.Concept.objects.filter(
        concept_name__icontains=query
    ).values("concept_id")
    return db.rows(
        models.EventsLong.objects.filter(concept_id__in=matching_concepts)
        .values("domain_id")
        .annotate(
            medical_concepts=Count("concept_id", distinct=True),
            participants=Count("person_id", distinct=True),
        )
        .order_by("-participants", "domain_id")
    )


def domain_concepts(domain_id, query=None, limit=100, offset=0):
    concept_queryset = models.Concept.objects.filter(domain_id=domain_id)
    if query:
        concept_queryset = concept_queryset.filter(concept_name__icontains=query)

    concept_ids = concept_queryset.values("concept_id")
    participant_rows = db.rows(
        models.EventsLong.objects.filter(domain_id=domain_id, concept_id__in=concept_ids)
        .values("concept_id")
        .annotate(participants=Count("person_id", distinct=True))
        .order_by("-participants", "concept_id")
    )
    concept_map = {
        row["concept_id"]: row
        for row in db.rows(
            concept_queryset.values(
                "concept_id", "concept_name", "vocabulary_id", "concept_code"
            )
        )
    }
    cohort_size = models.DimPatient.objects.count()
    rows = []
    for item in participant_rows:
        concept = concept_map.get(item["concept_id"])
        if concept is None:
            continue
        participants = item["participants"]
        rows.append(
            {
                **concept,
                "participants": participants,
                "pct": participants / cohort_size * 100.0 if cohort_size else None,
            }
        )

    rows = sorted(rows, key=lambda row: (-row["participants"], row["concept_name"]))
    total = models.EventsLong.objects.filter(
        domain_id=domain_id, concept_id__in=concept_ids
    ).aggregate(total_participants=Count("person_id", distinct=True))
    return {
        "total_participants": total["total_participants"],
        "data": rows[offset : offset + limit],
    }
