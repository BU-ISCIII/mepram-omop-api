from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class DomainQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=False)


class DomainConceptQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class ConceptQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=False)
    domain_id = serializers.CharField(required=False, allow_blank=False)
    vocabulary_id = serializers.CharField(required=False, allow_blank=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class ConceptDetailQuerySerializer(serializers.Serializer):
    event_type = serializers.CharField(required=False, allow_blank=False)


class MeasurementQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=False)
    concept_id = serializers.IntegerField(required=False, min_value=1)
    event_type = serializers.CharField(required=False, allow_blank=False)
    stratification = serializers.ChoiceField(
        required=False,
        choices=["none", "age", "sex", "age_sex"],
        default="none",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class FactConceptQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=False)
    domain_id = serializers.CharField(required=False, allow_blank=False)
    event_type = serializers.CharField(required=False, allow_blank=False)
    stratification = serializers.ChoiceField(
        required=False,
        choices=["none", "age", "sex", "age_sex"],
        default="none",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class HealthTableSerializer(serializers.Serializer):
    table = serializers.CharField()
    exists = serializers.BooleanField(allow_null=True)
    row_count = serializers.IntegerField(allow_null=True)


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    schema = serializers.CharField()
    tables = HealthTableSerializer(many=True)
    checked_at = serializers.CharField()


class DomainSerializer(serializers.Serializer):
    domain_id = serializers.CharField()
    medical_concepts = serializers.IntegerField()
    participants = serializers.IntegerField()


class ConceptSerializer(serializers.Serializer):
    concept_id = serializers.IntegerField()
    concept_name = serializers.CharField(allow_null=True)
    domain_id = serializers.CharField(allow_null=True)
    vocabulary_id = serializers.CharField(allow_null=True)
    concept_code = serializers.CharField(allow_null=True)


class DomainConceptSerializer(ConceptSerializer):
    participants = serializers.IntegerField()
    pct = serializers.FloatField(allow_null=True)


class DomainConceptResponseSerializer(serializers.Serializer):
    domain_id = serializers.CharField()
    total_participants = serializers.IntegerField()
    data = DomainConceptSerializer(many=True)


class MetadataResponseSerializer(serializers.Serializer):
    schema = serializers.CharField()
    domains = DomainSerializer(many=True)
    event_types = serializers.ListField(child=serializers.CharField())
    age_groups = serializers.ListField(child=serializers.CharField())
    genders = serializers.ListField(child=serializers.CharField())
    vocabularies = serializers.ListField(child=serializers.CharField())
    total_patients = serializers.IntegerField()
    capabilities = serializers.DictField()

class ReportQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=20)
    start_date = serializers.DateField(required=False, default="1980-01-01")
    end_date = serializers.DateField(required=False, default="3000-01-01")
    summary_name = serializers.CharField(required=False, allow_blank=True)

class PostReportQuerySerializer(serializers.Serializer):
    report_key = serializers.IntegerField()
    summary_name = serializers.CharField()
    scope_key = serializers.CharField()
    filters_hash = serializers.CharField()
    filters = serializers.JSONField(allow_null=True)
    payload = serializers.JSONField(required=True)
    created_at = serializers.DateField()
    updated_at = serializers.DateField()